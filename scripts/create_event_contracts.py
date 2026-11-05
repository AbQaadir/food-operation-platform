#!/usr/bin/env python3
import json
import os

CONTRACTS_DIR = "/Users/qaadir/Desktop/dev/foodOperationPlatform/contracts/events"
os.makedirs(CONTRACTS_DIR, exist_ok=True)

SCHEMAS = {
    "order.confirmed.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "OrderConfirmedEvent",
        "type": "object",
        "properties": {
            "orderId": { "type": "string", "format": "uuid" },
            "status": { "type": "string", "enum": ["CONFIRMED"] },
            "timestamp": { "type": "string" }
        },
        "required": ["orderId", "status"]
    },
    "order.cancelled.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "OrderCancelledEvent",
        "type": "object",
        "properties": {
            "orderId": { "type": "string", "format": "uuid" },
            "status": { "type": "string", "enum": ["CANCELLED"] },
            "reason": { "type": "string" },
            "timestamp": { "type": "string" }
        },
        "required": ["orderId", "status", "reason"]
    },
    "inventory.reserved.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "InventoryReservedEvent",
        "type": "object",
        "properties": {
            "orderId": { "type": "string", "format": "uuid" },
            "itemCount": { "type": "integer" }
        },
        "required": ["orderId", "itemCount"]
    },
    "inventory.rejected.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "InventoryRejectedEvent",
        "type": "object",
        "properties": {
            "orderId": { "type": "string", "format": "uuid" },
            "reason": { "type": "string" }
        },
        "required": ["orderId", "reason"]
    },
    "inventory.released.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "InventoryReleasedEvent",
        "type": "object",
        "properties": {
            "orderId": { "type": "string", "format": "uuid" },
            "releasedCount": { "type": "integer" }
        },
        "required": ["orderId", "releasedCount"]
    },
    "product.updated.schema.json": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "ProductUpdatedEvent",
        "type": "object",
        "properties": {
            "productId": { "type": "string", "format": "uuid" },
            "sku": { "type": "string" },
            "name": { "type": "string" },
            "price": { "type": "number" },
            "active": { "type": "boolean" }
        },
        "required": ["productId", "sku", "name", "price", "active"]
    }
}

for filename, schema in SCHEMAS.items():
    filepath = os.path.join(CONTRACTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Created {filepath}")

print("All event contract schemas created.")
