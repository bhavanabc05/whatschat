# import os
# import re
# import sys
# from groq import Groq
# from twilio.rest import Client
# from services.product_service import get_all_products, get_product_by_id
# venv_path = os.path.join(os.getcwd(), "venv", "Lib", "site-packages")
# if venv_path not in sys.path:
#     sys.path.append(venv_path)

# # 1. Setup Groq
# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# # 2. Setup Twilio (Bypassing the corrupted sub-modules)
# account_sid = os.getenv("TWILIO_ACCOUNT_SID")
# auth_token = os.getenv("TWILIO_AUTH_TOKEN")

# # We use a try-except here to catch the specific 'No module' error at startup
# try:
#     from twilio.rest import Client
# except ImportError:
#     print("❌ Critical: Twilio still not found in venv. Attempting global fallback...")
#     # This is a last-ditch effort to find it anywhere else on your PC
#     import subprocess
#     subprocess.check_call([sys.executable, "-m", "pip", "install", "twilio"])
#     from twilio.rest import Client

# def send_whatsapp_message(to, text, image_url=None):
#     try:
#         # Re-initialize inside the function if it failed at top
#         client = Client(account_sid, auth_token)
        
#         payload = {
#             "from_": os.getenv("TWILIO_NUMBER"),
#             "to": f"whatsapp:{to}",
#             "body": text
#         }
        
#         if image_url and image_url.startswith("http"):
#             payload["media_url"] = [image_url]

#         message = client.messages.create(**payload)
#         print(f"✅ Twilio Success! SID: {message.sid}")
        
#     except Exception as e:
#         print(f"❌ Twilio CRITICAL Error: {e}")
#         print("💡 TIP: Close terminal and run: pip install --upgrade twilio")

# def process_message(sender, user_input):
#     user_input = user_input.strip().lower()
    
#     # --- 1. INSTAGRAM & PRODUCT ID LOGIC ---
#     # Detects IDs like J-101 in the message
#     match = re.search(r'j-\d+', user_input)
#     if match:
#         product_id = match.group().upper()
#         product = get_product_by_id(product_id)
        
#         if product:
#             response_text = (
#                 f"💎 *{product['name']}*\n"
#                 f"💰 Price: {product['price']}\n\n"
#                 f"{product['description']}\n\n"
#                 "Type *'Buy'* to order or *'Link'* for the website! yarr"
#             )
#             return {"text": response_text, "image": product.get('image_url')}

#     # --- 2. MENU LOGIC ---
#     if user_input in ["hi", "hello", "hey", "start"]:
#         msg = (
#             "👋 *Welcome to AdaShop.24!* \n"
#             "Your AI Jewelry Assistant is online. \n\n"
#             "1️⃣ *Catalog:* See all pieces\n"
#             "2️⃣ *Cart:* View your bag\n"
#             "Just type what you're looking for!"
#         )
#         return {"text": msg, "image": None}

#     # --- 3. AI (GROQ) LOGIC ---
#     products = get_all_products()
#     # Format the product list for the AI to understand
#     inventory_str = "\n".join([f"- {p['name']} (ID: {p['id']}): {p['price']}" for p in products])
    
#     system_prompt = f"""
#     You are Ada, a witty Gen-Z jewelry expert.
#     Current Inventory:
#     {inventory_str}

#     Instructions:
#     - If they ask for a product, mention its ID.
#     - Be helpful, use emojis, and sound professional yet friendly.
#     """

#     completion = groq_client.chat.completions.create(
#         messages=[{"role": "system", "content": system_prompt},
#                   {"role": "user", "content": user_input}],
#         model="llama-3.1-8b-instant",
#     )
    
#     return {"text": completion.choices[0].message.content, "image": None}



import os
import re
import sys
from groq import Groq
from twilio.rest import Client
from services.product_service import get_all_products, get_product_by_id

# --- SESSION TRACKER ---
# This remembers which product the user last looked at
user_sessions = {} 

# 1. Setup Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 2. Setup Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

def send_whatsapp_message(to, text, image_url=None):
    try:
        client = Client(account_sid, auth_token)
        payload = {
            "from_": os.getenv("TWILIO_NUMBER"),
            "to": f"whatsapp:{to}",
            "body": text
        }
        if image_url and image_url.startswith("http"):
            payload["media_url"] = [image_url]

        message = client.messages.create(**payload)
        print(f"✅ Twilio Success! SID: {message.sid}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

def process_message(sender, user_input,user_name="Friend"):
    user_input = user_input.strip().lower()
    
    # --- 1. ORDER CONFIRMATION LOGIC ---
    if user_input == "buy":
        # Check if we remember what product this user was looking at
        last_product_id = user_sessions.get(sender)
        
        if last_product_id:
            product = get_product_by_id(last_product_id)
            # Clear the session after ordering
            user_sessions.pop(sender, None) 
            
            confirm_msg = (
                f"🎉 *ORDER CONFIRMED!* \n\n"
                f"Item: {product['name']}\n"
                f"Amount: {product['price']}\n\n"
                f"Your order has been placed successfully. We'll send the tracking link to this chat soon! ✨"
            )
            return {"text": confirm_msg, "image": None}
        else:
            return {"text": "Oops! Which item would you like to buy? Please mention the ID (e.g., J-101).", "image": None}

    # --- 2. PRODUCT DETECTION LOGIC ---
    match = re.search(r'[a-f0-9]{24}', user_input)
    if match:
        product_id = match.group()
        product = get_product_by_id(product_id)
        
        if product:
            # SAVE the product ID to the user's session
            user_sessions[sender] = product_id 
            
            response_text = (
                f"💎 *{product['name']}*\n"
                f"💰 Price: {product['price']}\n\n"
                f"{product['description']}\n\n"
                "Reply with *'Buy'* to confirm your order now! 🛒"
            )
            return {"text": response_text, "image": product.get('image_url')}

    # --- 3. START/MENU LOGIC ---
    if user_input in ["hi", "hello", "hey", "start"]:
        msg = (
            f"👋 *Welcome to AdaShop.24, {user_name}!* \n"
            "Your AI Jewelry Assistant is online. \n\n"
            "Just type the name or ID of the jewelry you want to see!"
        )
        return {"text": msg, "image": None}

    # --- 4. AI (GROQ) LOGIC ---
    products = get_all_products()
    inventory_str = "\n".join([f"- {p['name']} (ID: {p['id']}): {p['price']}" for p in products])
    
    system_prompt = f"""
    You are Ada, a witty Gen-Z jewelry expert. 
    You are currently chatting with a customer named {user_name}. Address them by their name naturally in your responses!
    If a user wants to buy something or see details, tell them to reply with the EXACT Product ID.
    Inventory: {inventory_str}
    """

    completion = groq_client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_input}],
        model="llama-3.1-8b-instant",
    )
    
    return {"text": completion.choices[0].message.content, "image": None}