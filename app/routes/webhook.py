from fastapi import APIRouter, Form
from services.ai_service import process_message, send_whatsapp_message, transcribe_audio

router = APIRouter()

@router.post("/webhook")
async def webhook(
    From: str = Form(...), 
    Body: str = Form(""), # Make this default to empty, since voice notes have no text body
    ProfileName: str = Form("Friend"),
    NumMedia: int = Form(0),              # Detects if media is attached
    MediaContentType0: str = Form(""),    # Detects the type (e.g., audio/ogg)
    MediaUrl0: str = Form("")             # The URL to the file
):
    try:
        sender_id = From.replace("whatsapp:", "").replace("messenger:", "")
        message_body = Body.strip()

        # --- 🎙️ VOICE NOTE LOGIC ---
        if NumMedia > 0 and "audio" in MediaContentType0:
            print(f"🎙️ Voice note received from {ProfileName}! Transcribing...")
            
            # Convert voice to text!
            transcribed_text = transcribe_audio(MediaUrl0)
            
            if transcribed_text:
                print(f"📝 Transcription: '{transcribed_text}'")
                message_body = transcribed_text
            else:
                message_body = "Sorry, my ears are a bit blocked. Could you type that out? 😅"

        # If they sent an image/video instead of text/audio, just ignore it for now
        if not message_body:
            return {"status": "success"}

        # --- NORMAL PROCESSING ---
        # Whether it was typed or spoken, it's just text now! Pass it to your AI.
        result = process_message(sender_id, message_body, ProfileName)

        send_whatsapp_message(
            to=sender_id, 
            text=result.get('text', "Sorry, I encountered an error."), 
            image_url=result.get('image')
        )

        print(f"📩 Processed for {ProfileName}: {message_body}")
        
        return {"status": "success"}

    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return {"status": "error", "message": str(e)}