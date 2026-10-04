import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.tools import list_low_stock_products, get_daily_sales

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"

@pytest.mark.asyncio
async def test_tools():
    low_stock = await list_low_stock_products(10)
    assert "items" in low_stock
    assert len(low_stock["items"]) > 0

    sales = await get_daily_sales("today")
    assert sales["total_revenue"] > 0
    assert sales["total_orders"] > 0

def test_chat_stream():
    payload = {
        "messages": [
            {"role": "user", "content": "What is the stock level of product a68d0d41-c837-4da4-8c66-e64f5ea6e761?"}
        ]
    }
    response = client.post("/api/v1/ai/chat", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    text = response.text
    assert "event: token" in text
    assert "event: done" in text

def test_assistant_chat_json():
    payload = {
        "message": "Which warehouse has the most low-stock items?",
        "conversationId": "test-conv-123"
    }
    response = client.post("/api/v1/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "toolCalls" in data
    assert data["conversationId"] == "test-conv-123"

