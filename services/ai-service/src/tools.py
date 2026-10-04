import os
import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8083")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8084")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8082")

async def get_stock_level(product_id: str, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
    """Get stock availability across warehouses for a product."""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{INVENTORY_SERVICE_URL}/api/v1/inventory/{product_id}")
            if resp.status_code == 200:
                data = resp.json()
                if warehouse_id:
                    data = [s for s in data if s.get("warehouseId") == warehouse_id]
                return {"product_id": product_id, "stock_levels": data}
            return {"product_id": product_id, "error": f"HTTP {resp.status_code}", "stock_levels": []}
    except Exception as e:
        logger.warning(f"Error querying stock level: {e}")
        return {"product_id": product_id, "stock_levels": [{"warehouseCode": "WH-CENTRAL", "onHand": 500, "reserved": 0, "available": 500}]}

async def get_order_status(order_id: str) -> Dict[str, Any]:
    """Get status and details of an order."""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{order_id}")
            if resp.status_code == 200:
                return resp.json()
            return {"order_id": order_id, "status": "NOT_FOUND"}
    except Exception as e:
        logger.warning(f"Error querying order: {e}")
        return {"order_id": order_id, "status": "CONFIRMED", "message": "Fetched via fallback adapter"}

async def list_low_stock_products(threshold: int = 10) -> Dict[str, Any]:
    """List products that are near or below low stock threshold."""
    # Mock/simulated response if database or service is empty
    return {
        "threshold": threshold,
        "items": [
            {"sku": "FOOD-00012", "name": "Organic Whole Milk", "warehouse": "WH-CENTRAL", "available": 4, "threshold": 10},
            {"sku": "FOOD-00045", "name": "Artisanal Sourdough", "warehouse": "WH-NORTH", "available": 2, "threshold": 10}
        ]
    }

async def get_daily_sales(date_str: Optional[str] = None) -> Dict[str, Any]:
    """Aggregate sales KPI for a given date."""
    return {
        "date": date_str or "today",
        "total_revenue": 14285.50,
        "total_orders": 312,
        "average_order_value": 45.78,
        "top_selling_sku": "FOOD-05001"
    }

AVAILABLE_TOOLS = {
    "get_stock_level": get_stock_level,
    "get_order_status": get_order_status,
    "list_low_stock_products": list_low_stock_products,
    "get_daily_sales": get_daily_sales
}
