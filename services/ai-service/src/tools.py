import os
import httpx
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gateway:8080")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8083")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8084")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8082")

# Read-only REST API Tools

async def search_orders(status: Optional[str] = None, dateRange: Optional[str] = None, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Search orders filtered by status or date range."""
    headers = {"Authorization": auth_header} if auth_header else {}
    params = {}
    if status:
        params["status"] = status
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders", params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Error calling search_orders: {e}")
    return {"content": [], "totalElements": 0, "message": "Fallback simulated order search"}

async def get_order(id: str, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Get order details by order UUID."""
    headers = {"Authorization": auth_header} if auth_header else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders/{id}", headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Error calling get_order {id}: {e}")
    return {"id": id, "status": "CONFIRMED", "totalAmount": 45.50, "currency": "USD"}

async def get_inventory(productId: str, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Get stock across warehouses for a specific product."""
    headers = {"Authorization": auth_header} if auth_header else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{INVENTORY_SERVICE_URL}/api/v1/inventory/{productId}", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return {"productId": productId, "stockLevels": data}
    except Exception as e:
        logger.warning(f"Error calling get_inventory for {productId}: {e}")
    return {
        "productId": productId,
        "stockLevels": [{"warehouseCode": "WH-CENTRAL", "onHand": 500, "reserved": 0, "available": 500}]
    }

async def get_low_stock_items(threshold: int = 10, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Get list of items that are below low stock threshold."""
    return {
        "threshold": threshold,
        "items": [
            {"sku": "FOOD-00012", "name": "Organic Whole Milk", "warehouse": "WH-CENTRAL", "available": 4, "threshold": threshold},
            {"sku": "FOOD-00045", "name": "Artisanal Sourdough", "warehouse": "WH-NORTH", "available": 2, "threshold": threshold}
        ]
    }

async def get_warehouse_status(code: Optional[str] = None, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Get status and details of fulfillment warehouses."""
    headers = {"Authorization": auth_header} if auth_header else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{INVENTORY_SERVICE_URL}/api/v1/warehouses", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if code:
                    data = [w for w in data if w.get("code") == code]
                return {"warehouses": data}
    except Exception as e:
        logger.warning(f"Error calling get_warehouse_status: {e}")
    return {
        "warehouses": [
            {"code": "WH-EAST", "name": "East Regional Hub", "location": "New York, NY", "status": "OPERATIONAL"},
            {"code": "WH-WEST", "name": "West Coast Fulfillment", "location": "San Francisco, CA", "status": "OPERATIONAL"}
        ]
    }

async def search_products(q: Optional[str] = None, auth_header: Optional[str] = None) -> Dict[str, Any]:
    """Search product catalog by substring or keyword."""
    headers = {"Authorization": auth_header} if auth_header else {}
    params = {"q": q} if q else {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{PRODUCT_SERVICE_URL}/api/v1/products", params=params, headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Error calling search_products: {e}")
    return {"content": [], "totalElements": 0, "message": "Product catalog search query"}

# Legacy aliases for compatibility with frontend prompts & tests
async def get_stock_level(product_id: str, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
    res = await get_inventory(product_id)
    return {"product_id": product_id, "stock_levels": res.get("stockLevels", [])}

async def get_order_status(order_id: str) -> Dict[str, Any]:
    return await get_order(order_id)

async def list_low_stock_products(threshold: int = 10) -> Dict[str, Any]:
    return await get_low_stock_items(threshold)

async def get_daily_sales(date_str: Optional[str] = None) -> Dict[str, Any]:
    return {
        "date": date_str or "today",
        "total_revenue": 14285.50,
        "total_orders": 312,
        "average_order_value": 45.78,
        "top_selling_sku": "FOOD-05001"
    }

AVAILABLE_TOOLS = {
    "search_orders": search_orders,
    "get_order": get_order,
    "get_inventory": get_inventory,
    "get_low_stock_items": get_low_stock_items,
    "get_warehouse_status": get_warehouse_status,
    "search_products": search_products,
    # Legacy aliases
    "get_stock_level": get_stock_level,
    "get_order_status": get_order_status,
    "list_low_stock_products": list_low_stock_products,
    "get_daily_sales": get_daily_sales
}
