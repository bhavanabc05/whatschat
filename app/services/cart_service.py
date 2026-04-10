import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["shop"]
carts_collection = db["carts"]

def get_user_cart(sender):
    """Retrieves a user's cart or creates an empty one if it doesn't exist."""
    cart = carts_collection.find_one({"sender": sender}, {"_id": 0})
    if not cart:
        cart = {"sender": sender, "items": [], "total": 0}
        carts_collection.insert_one({"sender": sender, "items": [], "total": 0})
    return cart

def add_to_cart(sender, product):
    """Adds a product to the user's cart and updates the total."""
    price_str = str(product.get("price", "0"))
    numeric_price = int(''.join(filter(str.isdigit, price_str)) or 0)

    item = {
        "id": product["id"],
        "name": product["name"],
        "price": numeric_price
    }

    # Update the cart AND set the 'updated_at' timestamp
    carts_collection.update_one(
        {"sender": sender},
        {
            "$push": {"items": item},
            "$inc": {"total": numeric_price},
            "$set": {"updated_at": datetime.utcnow()} # <-- Add this line
        },
        upsert=True
    )
    return True

def clear_cart(sender):
    """Empties the cart after a successful checkout."""
    carts_collection.update_one(
        {"sender": sender},
        {"$set": {"items": [], "total": 0}}
    )