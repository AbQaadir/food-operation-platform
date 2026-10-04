import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from src.agent import OperationsAssistant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Food Operations AI Assistant API",
    description="Tool-calling operations AI assistant with streaming SSE support",
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

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

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
async def chat_stream(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    logger.info(f"Incoming chat request with {len(messages)} messages")

    return StreamingResponse(
        assistant.stream_chat(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
