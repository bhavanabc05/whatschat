from fastapi import APIRouter, Form
from services.ai_service import process_message, send_whatsapp_message

router = APIRouter()

@router.post("/webhook")
async def webhook(
    From: str = Form(...), 
    Body: str = Form(...),
    ProfileName: str = Form("Friend")  # 1. Add ProfileName here
):
    """
    Handles incoming WhatsApp/Instagram messages from Twilio.
    """
    try:
        sender_id = From.replace("whatsapp:", "").replace("messenger:", "")
        message_body = Body

        # 2. Pass the ProfileName to your AI service
        result = process_message(sender_id, message_body, ProfileName)

        send_whatsapp_message(
            to=sender_id, 
            text=result.get('text', "Sorry, I encountered an error."), 
            image_url=result.get('image')
        )

        print(f"📩 Incoming from {ProfileName} ({sender_id}): {message_body}")
        
        return {"status": "success"}

    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "message": str(e)}