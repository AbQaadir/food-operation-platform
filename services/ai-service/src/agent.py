import json
import os
import asyncio
from typing import AsyncGenerator, List, Dict, Any
from src.tools import AVAILABLE_TOOLS

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

class OperationsAssistant:

    async def stream_chat(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        user_message = messages[-1].get("content", "").lower() if messages else ""

        # Check intent for tool execution
        tool_to_call = None
        tool_args = {}

        if "stock" in user_message or "inventory" in user_message:
            if "low" in user_message:
                tool_to_call = "list_low_stock_products"
                tool_args = {"threshold": 10}
            else:
                tool_to_call = "get_stock_level"
                # Extract UUID or sample product
                words = user_message.split()
                pid = next((w for w in words if "-" in w and len(w) == 36), "a68d0d41-c837-4da4-8c66-e64f5ea6e761")
                tool_args = {"product_id": pid}

        elif "order" in user_message or "status" in user_message:
            tool_to_call = "get_order_status"
            words = user_message.split()
            oid = next((w for w in words if "-" in w and len(w) == 36), "12389a41-8375-42ef-9344-dae519c8c2ac")
            tool_args = {"order_id": oid}

        elif "sales" in user_message or "revenue" in user_message or "kpi" in user_message:
            tool_to_call = "get_daily_sales"
            tool_args = {"date_str": "today"}

        # 1. Emit tool call if identified
        tool_result = None
        if tool_to_call and tool_to_call in AVAILABLE_TOOLS:
            yield f"event: tool_call\ndata: {json.dumps({'tool': tool_to_call, 'args': tool_args})}\n\n"
            await asyncio.sleep(0.1)
            tool_func = AVAILABLE_TOOLS[tool_to_call]
            tool_result = await tool_func(**tool_args)
            yield f"event: tool_result\ndata: {json.dumps({'tool': tool_to_call, 'result': tool_result})}\n\n"
            await asyncio.sleep(0.1)

        # 2. Stream natural language tokens
        yield f"event: token\ndata: {json.dumps({'chunk': 'Hello! '})}\n\n"
        await asyncio.sleep(0.05)

        if tool_result:
            if tool_to_call == "get_stock_level":
                stocks = tool_result.get("stock_levels", [])
                total_avail = sum(s.get("available", 0) for s in stocks) if isinstance(stocks, list) else 0
                explanation = f"I inspected inventory for product {tool_args.get('product_id')}. Across warehouses, there are currently {total_avail} units available."
            elif tool_to_call == "get_order_status":
                status = tool_result.get("status", "UNKNOWN")
                total = tool_result.get("totalAmount", 0)
                explanation = f"Order #{tool_args.get('order_id')} is currently in {status} status with total amount ${total}."
            elif tool_to_call == "list_low_stock_products":
                count = len(tool_result.get("items", []))
                explanation = f"Found {count} products currently below the low stock threshold of {tool_args.get('threshold')} units."
            elif tool_to_call == "get_daily_sales":
                rev = tool_result.get("total_revenue", 0)
                orders = tool_result.get("total_orders", 0)
                explanation = f"Today's operations report: ${rev:,.2f} total revenue across {orders} completed orders."
            else:
                explanation = f"Tool execution result: {json.dumps(tool_result)}"
        else:
            explanation = "I am the Food Operations AI Assistant. I can check warehouse stock levels, track order statuses, highlight low-inventory items, and summarize daily revenue metrics."

        # Stream explanation word by word
        words = explanation.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield f"event: token\ndata: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.03)

        # 3. Emit done event
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
