import os
import re
import sys
import requests
from groq import Groq
from twilio.rest import Client
from services.product_service import get_all_products, get_product_by_id,search_products
from services.cart_service import get_user_cart, add_to_cart, clear_cart
from services.order_service import create_order, get_recent_order


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
        
        # Check if we are sending a list of images (for the welcome message) 
        # or a single string (for a specific product)
        if isinstance(image_url, list) and len(image_url) > 0:
            payload["media_url"] = [url for url in image_url if url]
        elif isinstance(image_url, str) and image_url.startswith("http"):
            payload["media_url"] = [image_url]

        message = client.messages.create(**payload)
        print(f"✅ Twilio Success! SID: {message.sid}")
    except Exception as e:
        print(f"❌ Twilio Error: {e}")

def transcribe_audio(media_url):
    """Downloads audio from Twilio and transcribes it using Groq."""
    try:
        # 1. Download the audio file from Twilio (requires auth)
        response = requests.get(media_url, auth=(account_sid, auth_token))
        
        if response.status_code == 200:
            # 2. Save it temporarily
            temp_file = "temp_voice.ogg"
            with open(temp_file, "wb") as f:
                f.write(response.content)
            
            # 3. Send to Groq Whisper API
            with open(temp_file, "rb") as file:
                transcription = groq_client.audio.transcriptions.create(
                  file=(temp_file, file.read()),
                  model="whisper-large-v3",
                )
            
            # 4. Clean up the temp file
            os.remove(temp_file)
            return transcription.text
            
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
    return None

def process_message(sender, user_input, user_name="Friend"):
    user_input = user_input.strip().lower()
    
    # --- 1. CART MANAGEMENT LOGIC ---
    if user_input in ["cart", "bag", "my cart"]:
        cart = get_user_cart(sender)
        if not cart["items"]:
            return {"text": "🛒 Your cart is currently empty! Type 'Hi' to see our favorites.", "image": None}
        
        # Build a receipt-style string
        items_str = "\n".join([f"▪️ {item['name']} - ₹{item['price']}" for item in cart["items"]])
        msg = (
            f"🛒 *{user_name}'s Cart*\n\n"
            f"{items_str}\n\n"
            f"💰 *Total: ₹{cart['total']}*\n\n"
            "Ready to order? Reply with *Checkout*! ✅"
        )
        return {"text": msg, "image": None}

    # --- 2. CHECKOUT LOGIC ---
    if user_input in ["checkout", "buy", "pay"]:
        cart = get_user_cart(sender)
        if not cart["items"]:
            return {"text": "Your cart is empty! Nothing to checkout yet.", "image": None}
        
        total = cart["total"]
        
        # Save the order to MongoDB!
        order_id = create_order(sender, cart["items"], total)
        
        # Now clear the cart
        clear_cart(sender)
        
        confirm_msg = (
            f"🎉 *ORDER SUCCESSFUL, {user_name}!* \n\n"
            f"Order ID: {order_id[-6:].upper()}\n" # Display just the last 6 chars for a clean look
            f"Your order total of *₹{total}* has been received.\n\n"
            "Type *'Track Order'* anytime to see your shipping status! ✨"
        )
        return {"text": confirm_msg, "image": None}
    
    # --- 3. ORDER TRACKING LOGIC ---
    if user_input in ["track order", "track", "status", "where is my order"]:
        recent_order = get_recent_order(sender)
        
        if not recent_order:
            return {"text": "I couldn't find any recent orders for your number. Have you shopped with us before? 🛍️", "image": None}

        # Format the items neatly
        items_str = ", ".join([item['name'] for item in recent_order['items']])
        status = recent_order.get('status', 'Processing')
        
        msg = (
            f"📦 *Order Status Update*\n\n"
            f"Items: {items_str}\n"
            f"Total: ₹{recent_order['total']}\n"
            f"Current Status: *{status}* 🚚\n\n"
            "We'll notify you when it's out for delivery!"
        )
        return {"text": msg, "image": None}

    # --- 4. ADD TO CART LOGIC ---
    if user_input == "add":
        last_product_id = user_sessions.get(sender)
        if last_product_id:
            product = get_product_by_id(last_product_id)
            add_to_cart(sender, product)
            # Remove from session so they don't accidentally add it twice
            user_sessions.pop(sender, None) 
            
            return {
                "text": f"✅ *{product['name']}* added to your cart!\n\nType *Cart* to view your bag, or keep exploring IDs.", 
                "image": None
            }
        else:
            return {"text": "Oops! Which item did you want to add? Please view an item by its ID first.", "image": None}

    # --- 5. PRODUCT DETECTION LOGIC ---
    match = re.search(r'[a-f0-9]{24}', user_input)
    if match:
        product_id = match.group()
        product = get_product_by_id(product_id)
        
        if product:
            user_sessions[sender] = product_id 
            
            response_text = (
                f"💎 *{product['name']}*\n"
                f"💰 Price: {product['price']}\n\n"
                f"{product['description']}\n\n"
                "Reply with *'Add'* to put this in your cart! 🛍️"
            )
            return {"text": response_text, "image": product.get('image_url')}

    # --- 6. START/MENU LOGIC ---
    if user_input in ["hi", "hello", "hey", "start", "menu"]:
        products = get_all_products()
        featured_images = [p["image_url"] for p in products if p.get("image_url")][:4]
        
        msg = (
            f"👋 *Welcome to AdaShop.24, {user_name}!* \n"
            "Your AI Jewelry Assistant is online. ✨\n\n"
            "Tap the grid below to swipe through our favorites!\n"
            "Type a Product ID to view it, or type *Cart* to see your bag."
        )
        return {"text": msg, "image": featured_images}

    # --- 7. AI (GROQ) LOGIC ---
    products = get_all_products()
    inventory_str = "\n".join([f"- {p['name']} (ID: {p['id']}): {p['price']}" for p in products])
    
    system_prompt = f"""
    You are Ada, a witty Gen-Z jewelry expert chatting with {user_name}.
    
    CRITICAL SYSTEM OVERRIDE:
    You are connected to a live database. Whenever the user expresses ANY interest in viewing, browsing, or finding jewelry (even vague requests), YOU MUST NOT reply with conversational text. 
    You MUST trigger a search by replying ONLY with this exact format:
    [SEARCH] category: <item_type_or_any>, max_price: <number_or_any>
    
    HOW TO RESPOND (EXAMPLES):
    User: "Hi do you have bracelet collection?"
    Output: [SEARCH] category: bracelet, max_price: any
    
    User: "Show me few pieces from your catalog"
    Output: [SEARCH] category: any, max_price: any
    
    User: "I am looking for pearl necklace"
    Output: [SEARCH] category: pearl necklace, max_price: any
    
    User: "What's in my bag?"
    Output: Type "Cart" to see your bag!
    
    Do NOT write introductory or conversational text if the user wants to see products. ONLY output the [SEARCH] string.
    """

    completion = groq_client.chat.completions.create(
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_input}],
        model="llama-3.1-8b-instant",
    )
    
    ai_response = completion.choices[0].message.content.strip()

    # --- 7. THE INTERCEPTOR ---
    if "[SEARCH]" in ai_response:
        try:
            # Clean the string and extract the data
            search_str = ai_response.replace("[SEARCH]", "").strip()
            parts = search_str.split(",")
            
            category = parts[0].split(":")[1].strip()
            max_price_str = parts[1].split(":")[1].strip()
            
            max_price = int(max_price_str) if max_price_str.isdigit() else None
            
            # Hit the database!
            results = search_products(category, max_price)
            
            if not results:
                return {"text": f"Aw man, I couldn't find any {category}s matching that vibe! 🥺 Try searching for something else?", "image": None}
                
            # Build the response with the WhatsApp Album
            res_text = f"✨ Here's what I found for '{category}':\n\n"
            images = []
            
            for r in results:
                res_text += f"💎 *{r['name']}* - {r['price']}\nID: {r['id']}\n\n"
                if r['image_url']: 
                    images.append(r['image_url'])
                
            res_text += "Type the ID of the one you like to view it! 🛍️"
            
            return {"text": res_text, "image": images}
            
        except Exception as e:
            print(f"Search Parsing Error: {e}")
            return {"text": "Oops, my search brain glitched! Can you try asking that differently? 😅", "image": None}

    # If it wasn't a search, return the normal AI text
    return {"text": ai_response, "image": None}