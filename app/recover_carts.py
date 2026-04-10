import os
import sys
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.ai_service import send_whatsapp_message

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["shop"]
carts_collection = db["carts"]

def run_cart_recovery():
    print("\n🛒 --- AdaShop.24 Abandoned Cart Recovery --- 🛒\n")
    print("Scanning database for abandoned carts...")
    
    # Find carts that have at least 1 item in the 'items' array
    abandoned_carts = list(carts_collection.find({"items": {"$not": {"$size": 0}}}))
    
    if not abandoned_carts:
        print("✅ All clear! No abandoned carts found.")
        return

    print(f"⚠️ Found {len(abandoned_carts)} abandoned cart(s). Sending reminders...\n")
    
    for cart in abandoned_carts:
        user_number = cart['sender']
        items = cart['items']
        
        # Grab the name of the first item to make the message personal
        first_item_name = items[0]['name']
        extra_items = len(items) - 1
        
        item_text = f"*{first_item_name}*"
        if extra_items > 0:
            item_text += f" and {extra_items} other item(s)"

        message = (
            f"👋 Hey there! We noticed you left {item_text} in your bag. \n\n"
            f"They're selling out fast! ⏳\n\n"
            f"Reply with *Cart* to review your bag, or *Checkout* to complete your order instantly. ✨"
        )
        
        print(f"📲 Sending reminder to {user_number}...")
        send_whatsapp_message(to=user_number, text=message)
        
    print("\n✅ Cart recovery sequence complete!\n")

if __name__ == "__main__":
    run_cart_recovery()