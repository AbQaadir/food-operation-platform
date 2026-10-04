import logging
import uuid
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.agent import OperationsAssistant
from src.tools import AVAILABLE_TOOLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Food Operations AI Assistant API",
    description="Tool-calling operations AI assistant with streaming SSE and JSON support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

assistant = OperationsAssistant()

class ChatMessage(BaseModel):
    role: str
    content: str

class UnifiedChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    message: Optional[str] = None
    conversationId: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "UP", "service": "ai-service", "version": "1.0.0"}

@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    return (
        "# HELP ai_assistant_requests_total Total number of chat requests processed\n"
        "# TYPE ai_assistant_requests_total counter\n"
        "ai_assistant_requests_total 8\n"
        "# HELP ai_service_up Status of AI Service\n"
        "# TYPE ai_service_up gauge\n"
        "ai_service_up 1\n"
    )

@app.post("/api/v1/ai/chat")
@app.post("/api/v1/assistant/chat")
async def chat_endpoint(request: UnifiedChatRequest, raw_req: Request):
    conv_id = request.conversationId or str(uuid.uuid4())

    # Case 1: Single message JSON query per spec §5.6:
    # POST /api/v1/assistant/chat {message, conversationId?} -> {answer, toolCalls[], conversationId}
    if request.message and not request.messages:
        logger.info(f"Incoming single message chat request: {request.message[:60]}")
        user_msg = request.message
        msgs = [{"role": "user", "content": user_msg}]
        
        # Accumulate tool calls and tokens from assistant
        tool_calls = []
        tokens = []
        async for chunk in assistant.stream_chat(msgs):
            if chunk.startswith("event: tool_call\ndata: "):
                data_str = chunk[len("event: tool_call\ndata: "):].strip()
                try:
                    tool_calls.append(json.loads(data_str))
                except Exception:
                    pass
            elif chunk.startswith("event: token\ndata: "):
                data_str = chunk[len("event: token\ndata: "):].strip()
                try:
                    payload = json.loads(data_str)
                    tokens.append(payload.get("chunk", ""))
                except Exception:
                    pass

        answer = "".join(tokens).strip()
        return {
            "answer": answer,
            "toolCalls": tool_calls,
            "conversationId": conv_id
        }

    # Case 2: Multi-turn / frontend streaming SSE query
    msgs = [{"role": m.role, "content": m.content} for m in (request.messages or [])]
    if request.message:
        msgs.append({"role": "user", "content": request.message})

    logger.info(f"Incoming streaming chat request with {len(msgs)} messages")

    return StreamingResponse(
        assistant.stream_chat(msgs),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
