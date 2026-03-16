import httpx
import os
import tempfile
import traceback
from fastapi import HTTPException

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

async def send_whatsapp_message(to: str, message: str):
    if not PHONE_NUMBER_ID:
        print("[ERROR] WHATSAPP_PHONE_NUMBER_ID is not set! Cannot send messages.")
        return False
    if not WHATSAPP_TOKEN:
        print("[ERROR] WHATSAPP_TOKEN is not set! Cannot send messages.")
        return False

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                print(f"[ERROR] WhatsApp send failed ({response.status_code}): {response.text}")
                return False
            print(f"[OK] Message sent to {to}")
            return True
    except Exception as e:
        print(f"[ERROR] send_whatsapp_message exception: {e}")
        traceback.print_exc()
        return False

async def download_whatsapp_media(media_id: str):
    if not WHATSAPP_TOKEN:
        print("[ERROR] WHATSAPP_TOKEN is not set! Cannot download media.")
        return None

    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                print(f"[ERROR] Media metadata fetch failed ({response.status_code}): {response.text}")
                return None
            
            media_url = response.json().get("url")
            if not media_url:
                print("[ERROR] No media URL in response")
                return None
                
            media_response = await client.get(media_url, headers=headers)
            
            if media_response.status_code == 200:
                # Save to proper temp directory
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, f"wa_media_{media_id}.ogg")
                with open(file_path, "wb") as f:
                    f.write(media_response.content)
                print(f"[OK] Media downloaded to {file_path}")
                return file_path
            else:
                print(f"[ERROR] Media download failed ({media_response.status_code})")
                return None
    except Exception as e:
        print(f"[ERROR] download_whatsapp_media exception: {e}")
        traceback.print_exc()
        return None
