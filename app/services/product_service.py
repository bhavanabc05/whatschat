import os
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
BASE_URL = os.getenv("BASE_URL")

client = MongoClient(MONGO_URI)
db = client["shop"]
products_collection = db["products"]

def get_all_products():
    """Fetches all products for the AI to read."""
    products = list(products_collection.find({}))
    formatted_products = []
    
    for p in products:
        # Create the public image URL just like we do for single products
        image_path = p.get("imagePath", "")
        full_image_url = f"{BASE_URL}/{image_path}" if image_path else None
        
        formatted_products.append({
            "id": str(p["_id"]),
            "name": p.get("name", "Unknown"),
            "price": f"₹{p.get('price', 0)}",
            "image_url": full_image_url  # <-- Added this line
        })
    return formatted_products

def get_product_by_id(product_id):
    """Fetches a specific product by its MongoDB ObjectID."""
    try:
        p = products_collection.find_one({"_id": ObjectId(product_id)})
        if p:
            # Create a full public URL for Twilio to send the image
            image_path = p.get("imagePath", "")
            full_image_url = f"{BASE_URL}/{image_path}" if image_path else None
            
            return {
                "id": str(p["_id"]),
                "name": p.get("name", "Unknown"),
                "price": f"₹{p.get('price', 0)}",
                "description": p.get("description", ""),
                "image_url": full_image_url
            }
    except Exception as e:
        print(f"Database error: {e}")
    return None

def search_products(category=None, max_price=None):
    """Searches MongoDB dynamically based on AI-extracted parameters."""
    query = {}
    
    # 1. Search by name or description using Regex (case-insensitive)
    if category and category.lower() != "any":
        query["$or"] = [
            {"name": {"$regex": category, "$options": "i"}},
            {"description": {"$regex": category, "$options": "i"}}
        ]
        
    # 2. Filter by max price
    if max_price:
        query["price"] = {"$lte": int(max_price)}
        
    # Fetch up to 4 matching products (so we can trigger the WhatsApp Album UI)
    products = list(products_collection.find(query).limit(4))
    
    formatted_products = []
    for p in products:
        image_path = p.get("imagePath", "")
        full_image_url = f"{BASE_URL}/{image_path}" if image_path else None
        
        formatted_products.append({
            "id": str(p["_id"]),
            "name": p.get("name", "Unknown"),
            "price": f"₹{p.get('price', 0)}",
            "image_url": full_image_url
        })
    return formatted_products