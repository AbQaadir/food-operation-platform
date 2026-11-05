#!/usr/bin/env python3
"""
Seed script for Enterprise Food Operations Platform.
Generates >= 5,000 realistic food products and categories in product_db,
and seeds multi-warehouse fulfillment hubs and stock levels in inventory_db.
"""

import random
import subprocess
import sys
import uuid

CATEGORIES = [
    ("Bakery & Bread", "Fresh artisanal bread, pastries, and baked goods"),
    ("Dairy & Eggs", "Farm fresh dairy, milk, cheeses, butter, and eggs"),
    ("Meat & Poultry", "High quality beef, chicken, lamb, and pork cuts"),
    ("Seafood", "Wild caught and sustainably farmed fresh and frozen fish"),
    ("Fresh Produce", "Organic vegetables, fresh fruits, leafy greens, and herbs"),
    ("Pantry Staples", "Grains, pasta, cooking oils, vinegars, and spices"),
    ("Beverages", "Juices, sparkling waters, organic teas, and artisan coffees"),
    ("Frozen Foods", "Quick freeze meals, vegetables, desserts, and ice creams"),
    ("Snacks & Confectionery", "Nuts, dried fruits, energy bars, and chocolates"),
    ("Prepared & Deli", "Ready-to-eat salads, sandwiches, soups, and meal kits")
]

ADJECTIVES = [
    "Organic", "Artisanal", "Heritage", "Farm-Fresh", "Cold-Pressed",
    "Gourmet", "Gluten-Free", "Non-GMO", "Grass-Fed", "Wild-Caught",
    "Smoked", "Roasted", "Sun-Dried", "Handcrafted", "Raw",
    "Whole-Grain", "Aged", "Extra-Virgin", "Traditional", "Premium"
]

NOUNS = [
    "Sourdough Bread", "Croissant", "Baguette", "Whole Milk", "Cheddar Cheese",
    "Greek Yogurt", "Free-Range Eggs", "Salted Butter", "Ribeye Steak",
    "Chicken Breast", "Atlantic Salmon", "Alaskan Cod", "Avocado", "Heirloom Tomatoes",
    "Baby Spinach", "Extra Virgin Olive Oil", "Quinoa", "Basmati Rice",
    "Cold Brew Coffee", "Green Tea", "Dark Chocolate", "Roasted Almonds",
    "Sourdough Pretzel", "Honey Granola", "Fresh Pasta Sauce", "Black Truffle Oil",
    "Balsamic Glaze", "Pistachio Gelato", "Kombucha Ginger", "Apple Cider"
]

UNITS = ["KG", "L", "PACK", "BOX", "BOTTLE", "CAN", "UNIT"]

WAREHOUSES = [
    ("WH-EAST", "East Coast Logistics Hub", "New York, NY"),
    ("WH-WEST", "West Coast Distribution Hub", "Los Angeles, CA"),
    ("WH-CENTRAL", "Midwest Central Fulfillment Hub", "Chicago, IL"),
    ("WH-SOUTH", "Southern Cold Chain Hub", "Dallas, TX")
]

def run_psql(db: str, sql: str):
    cmd = [
        "docker", "exec", "-i", "food-platform-postgres",
        "psql", "-U", "postgres", "-d", db
    ]
    res = subprocess.run(cmd, input=sql, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error running SQL on {db}: {res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)
    return res.stdout

def seed_products():
    print("Checking product catalog seed (>= 5,000 items)...")
    
    count_check = run_psql("product_db", "SELECT COUNT(*) FROM products;")
    existing_count = 0
    for line in count_check.strip().split("\n"):
        line = line.strip()
        if line.isdigit():
            existing_count = int(line)
            break
            
    if existing_count >= 5000:
        print(f"Catalog already contains {existing_count} products. Skipping product generation.")
        return

    # Seed categories
    category_ids = []
    cat_sql_lines = ["BEGIN;"]
    for name, desc in CATEGORIES:
        cat_id = str(uuid.uuid4())
        category_ids.append(cat_id)
        escaped_name = name.replace("'", "''")
        cat_sql_lines.append(
            f"INSERT INTO categories (id, name, created_at) "
            f"VALUES ('{cat_id}', '{escaped_name}', NOW()) "
            f"ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name "
            f"RETURNING id;"
        )
    cat_sql_lines.append("COMMIT;")
    run_psql("product_db", "\n".join(cat_sql_lines))
    print(f"Seeded {len(CATEGORIES)} categories.")

    # Fetch actual category IDs from DB
    cat_rows = run_psql("product_db", "SELECT id FROM categories;").strip().split("\n")
    valid_cat_ids = [line.strip() for line in cat_rows if len(line.strip()) == 36 and "-" in line.strip()]
    if not valid_cat_ids:
        valid_cat_ids = category_ids

    target_count = 5200
    batch_size = 500
    total_inserted = 0

    print(f"Generating {target_count} products in batches of {batch_size}...")
    
    for batch_num in range(0, target_count, batch_size):
        sql_lines = ["BEGIN;"]
        current_batch = min(batch_size, target_count - batch_num)
        for i in range(current_batch):
            prod_num = batch_num + i + 1
            prod_id = str(uuid.uuid4())
            sku = f"FOOD-{prod_num:05d}"
            adj = random.choice(ADJECTIVES)
            noun = random.choice(NOUNS)
            name = f"{adj} {noun} #{prod_num}"
            escaped_name = name.replace("'", "''")
            desc = f"Delicious {adj.lower()} {noun.lower()} sourced from sustainable certified producers. SKU: {sku}."
            escaped_desc = desc.replace("'", "''")
            cat_id = random.choice(valid_cat_ids)
            unit = random.choice(UNITS)
            price = round(random.uniform(1.99, 149.99), 2)
            active = "TRUE" if random.random() > 0.05 else "FALSE"
            
            sql_lines.append(
                f"INSERT INTO products (id, sku, name, description, category_id, unit, price, currency, active, created_at, updated_at, version) "
                f"VALUES ('{prod_id}', '{sku}', '{escaped_name}', '{escaped_desc}', '{cat_id}', '{unit}', {price:.2f}, 'USD', {active}, NOW(), NOW(), 0) "
                f"ON CONFLICT (sku) DO NOTHING;"
            )
        sql_lines.append("COMMIT;")
        run_psql("product_db", "\n".join(sql_lines))
        total_inserted += current_batch
        print(f"  Inserted batch: {total_inserted}/{target_count} products")

    final_count = run_psql("product_db", "SELECT COUNT(*) FROM products;")
    print(f"Product seed complete! Current count: {final_count.strip()}")

def seed_warehouses_and_inventory():
    print("Checking warehouses in inventory_db...")
    wh_sql_lines = ["BEGIN;"]
    for code, name, location in WAREHOUSES:
        wh_id = str(uuid.uuid4())
        wh_sql_lines.append(
            f"INSERT INTO warehouses (id, code, name, location, created_at) "
            f"VALUES ('{wh_id}', '{code}', '{name}', '{location}', NOW()) "
            f"ON CONFLICT (code) DO NOTHING;"
        )
    wh_sql_lines.append("COMMIT;")
    run_psql("inventory_db", "\n".join(wh_sql_lines))

    # Fetch all warehouse IDs
    wh_out = run_psql("inventory_db", "SELECT id, code FROM warehouses;").strip().split("\n")
    warehouse_map = {}
    for line in wh_out:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 2 and len(parts[0]) == 36 and "-" in parts[0]:
            warehouse_map[parts[1]] = parts[0]

    print(f"Fulfillment warehouses registered: {list(warehouse_map.keys())}")

    # Fetch top 100 products from product_db to ensure inventory is available
    prod_out = run_psql("product_db", "SELECT id FROM products ORDER BY created_at ASC LIMIT 100;").strip().split("\n")
    product_ids = [line.strip() for line in prod_out if len(line.strip()) == 36 and "-" in line.strip()]

    print(f"Seeding stock allocations for {len(product_ids)} products across {len(warehouse_map)} warehouses...")
    stock_sql_lines = ["BEGIN;"]
    for pid in product_ids:
        for wh_code, wh_id in warehouse_map.items():
            stock_id = str(uuid.uuid4())
            on_hand = random.randint(150, 450)
            stock_sql_lines.append(
                f"INSERT INTO stock_levels (id, warehouse_id, product_id, on_hand, reserved, low_stock_threshold, version, created_at, updated_at) "
                f"VALUES ('{stock_id}', '{wh_id}', '{pid}', {on_hand}, 0, 15, 0, NOW(), NOW()) "
                f"ON CONFLICT (warehouse_id, product_id) DO UPDATE SET on_hand = EXCLUDED.on_hand WHERE stock_levels.on_hand = 0;"
            )
    stock_sql_lines.append("COMMIT;")
    run_psql("inventory_db", "\n".join(stock_sql_lines))

    stock_count = run_psql("inventory_db", "SELECT COUNT(*) FROM stock_levels;").strip().split("\n")
    print(f"Inventory seed complete! Total stock level entries: {stock_count[-1].strip()}")

def main():
    print("=== Enterprise Food Platform Seeder ===")
    seed_products()
    seed_warehouses_and_inventory()
    print("=== Seeding Successfully Completed ===")

if __name__ == "__main__":
    main()
