import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv
from services.pdf_service import generate_invoice

# Ensure we can import your existing Twilio function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.ai_service import send_whatsapp_message

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["shop"]
orders_collection = db["orders"]

def update_order_status():
    print("\n📦 --- AdaShop.24 Backend Admin --- 📦")
    
    # 1. Ask the admin for the details
    user_number = input("Enter User's WhatsApp Number (e.g., 919876543210): ")
    print("\nAvailable Statuses: \n1. Shipped 🚛\n2. Delivered 🎁")
    status_choice = input("Select new status (1 or 2): ")
    
    new_status = "Shipped" if status_choice == "1" else "Delivered" if status_choice == "2" else None
    
    if not new_status:
        print("❌ Invalid choice. Exiting.")
        return

    # 2. Find the user's most recent order
    recent_order = orders_collection.find_one(
        {"sender": user_number},
        sort=[("created_at", -1)]
    )
    
    if not recent_order:
        print(f"❌ No orders found for {user_number}")
        return
        
    order_id_short = str(recent_order['_id'])[-6:].upper()

    # 3. Update MongoDB
    orders_collection.update_one(
        {"_id": recent_order['_id']},
        {"$set": {"status": new_status}}
    )
    print(f"✅ Database updated: Order {order_id_short} is now {new_status}.")

    # 4. Generate PDF and Push Notification
    base_url = os.getenv("BASE_URL") # E.g., https://1a2b-3c4d.ngrok-free.app
    media_attachment = None

    if new_status == 'Shipped':
        message = f"🔔 *Order Update*\n\nGreat news! Your order ({order_id_short}) is now: *Shipped* 🚛\nIt is on the way!"
        
    elif new_status == 'Delivered':
        # Generate the PDF!
        pdf_filename = generate_invoice(recent_order)
        # Create the public Ngrok link to the PDF
        media_attachment = f"{base_url}/invoices/{pdf_filename}"
        
        message = (
            f"🎉 *Order Delivered!*\n\n"
            f"Your order ({order_id_short}) has safely arrived. 🎁\n"
            f"We have attached your official PDF invoice to this message.\n\n"
            f"Enjoy your jewelry!"
        )
    
    print("📲 Pushing WhatsApp notification...")
    # Twilio automatically recognizes the .pdf extension in the URL and sends it as a document!
    send_whatsapp_message(to=user_number, text=message, image_url=media_attachment)
    print("✅ Done!\n")

if __name__ == "__main__":
    update_order_status()