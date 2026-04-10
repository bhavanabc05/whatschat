import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["shop"]
orders_collection = db["orders"]

def create_order(sender, items, total):
    """Saves a new order to the database and returns the generated ID."""
    order = {
        "sender": sender,
        "items": items,
        "total": total,
        "status": "Processing", # All new orders start here
        "created_at": datetime.utcnow()
    }
    result = orders_collection.insert_one(order)
    return str(result.inserted_id)

def get_recent_order(sender):
    """Fetches the most recent order for a specific user."""
    # Sort by created_at descending (-1) to get the latest order
    order = orders_collection.find_one(
        {"sender": sender},
        sort=[("created_at", -1)]
    )
    return order