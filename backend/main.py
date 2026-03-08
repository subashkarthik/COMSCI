from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
import uvicorn
import os
import json
from dotenv import load_dotenv

# MUST load dot_env before importing services that rely on API keys
load_dotenv()

from services.whatsapp_handler import send_whatsapp_message, download_whatsapp_media
from services.transcription import transcribe_audio
from services.fact_checker import extract_claims, search_facts, generate_verdict

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WhatsApp Fact-Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"], # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy.orm import Session
from db.database import SessionLocal, FactCheck, init_db

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"DB Init error: {e}")

async def perform_fact_check_and_save(from_number: str, text: str, media_id: str, language: str):
    db: Session = SessionLocal()
    try:
        # 1. Repeat Claim Detection
        existing_check = db.query(FactCheck).filter(FactCheck.transcript == text).first()
        if existing_check:
            reply = f"""
🔁 *Repeat Claim Detected!*
✅ *Verdict:* {existing_check.verdict}
📊 *Confidence:* {existing_check.confidence}%

{existing_check.explanation}
            """
            await send_whatsapp_message(from_number, reply.strip())
            return

        # 2. Proceed with full pipeline
        claim = await extract_claims(text)
        search_results = await search_facts(claim)
        verdict_json = await generate_verdict(claim, search_results, language)
        verdict = json.loads(verdict_json)
        
        # 3. Save to DB for caching and dashboard
        new_check = FactCheck(
            whatsapp_id=media_id,
            from_number=from_number,
            claim=claim,
            transcript=text,
            verdict=verdict.get('Verdict'),
            confidence=verdict.get('Confidence Level'),
            virality_score=verdict.get('Virality Risk Score'),
            explanation=verdict.get('Explanation'),
            counter_message=verdict.get('Counter Message', ''),
            language=language
        )
        db.add(new_check)
        db.commit()
        
        # 4. Send Reply
        reply = f"""
📢 *Fact-Check Result*
✅ *Verdict:* {verdict['Verdict']}
📊 *Confidence:* {verdict['Confidence Level']}%
🔥 *Virality Risk:* {verdict['Virality Risk Score']}/10

*Reasoning:*
{verdict['Explanation']}

_Powered by Vernacular Fact-Checker_
        """
        if verdict.get('Counter Message'):
            reply += f"\n\n💬 *Counter-Message:*\n{verdict.get('Counter Message')}"
            
        await send_whatsapp_message(from_number, reply.strip())
    except Exception as e:
        print(f"Error in fact-checking logic: {e}")
        await send_whatsapp_message(from_number, "An error occurred during fact-checking.")
    finally:
        db.close()

async def process_media_message(from_number: str, media_id: str, media_type: str, caption: str = ""):
    try:
        # 1. Download Media
        file_path = await download_whatsapp_media(media_id)
        if not file_path:
            await send_whatsapp_message(from_number, "Failed to download media.")
            return
        
        text = ""
        language = "unknown"
        
        if media_type in ["audio", "voice"]:
            # 2. Transcribe
            text, language = await transcribe_audio(file_path)
        else:
            # 2. Image Vision Analysis
            from services.fact_checker import extract_claims_from_image
            claim = await extract_claims_from_image(file_path, caption)
            text = f"[Image Analysis]: {claim}"
            language = "Vision"
        
        await send_whatsapp_message(from_number, f"Processing {media_type} (detected {language})... 🕒")
        await perform_fact_check_and_save(from_number, text, media_id, language)
            
    except Exception as e:
        print(f"Error in media processing: {e}")
        await send_whatsapp_message(from_number, "An error occurred during media processing.")

async def process_text_message(from_number: str, text: str):
    await send_whatsapp_message(from_number, "Analyzing your text claim... 🕒")
    await perform_fact_check_and_save(from_number, text, "text_msg", "Text")

@app.get("/")
async def root():
    return {"message": "WhatsApp Fact-Checker API is running"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")
    
    verify_token = os.getenv("FASTAPI_VERIFY_TOKEN", "factcheck_token")
    
    if hub_mode == "subscribe" and hub_token == verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def handle_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    try:
        # WhatsApp Cloud API structure
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message = value.get("messages", [{}])[0]
        
        if not message:
            return {"status": "no message"}
        
        from_number = message.get("from")
        msg_type = message.get("type")
        
        if msg_type in ["audio", "voice"]:
            media_id = message.get(msg_type, {}).get("id")
            background_tasks.add_task(process_media_message, from_number, media_id, msg_type)
        
        elif msg_type == "image":
            media_id = message.get("image", {}).get("id")
            caption = message.get("image", {}).get("caption", "")
            background_tasks.add_task(process_media_message, from_number, media_id, "image", caption)
        
        elif msg_type == "text":
            text = message.get("text", {}).get("body")
            background_tasks.add_task(process_text_message, from_number, text)
            
    except Exception as e:
        print(f"Webhook Error: {e}")
    
    return {"status": "received"}

@app.post("/api/process_audio")
async def process_audio_endpoint(request: Request, background_tasks: BackgroundTasks):
    # Simulate processing an audio file upload
    # In a real app this would take a File(), but for the simulator we'll accept JSON with a transcript to mock the Whisper output
    data = await request.json()
    transcript = data.get("text")
    if not transcript:
        raise HTTPException(status_code=400, detail="Missing text in simulation payload")
        
    # Generate a dummy media_id and from_number for the simulator
    media_id = "simulated_" + transcript[:10]
    from_number = "Simulator_User"
    
    background_tasks.add_task(process_text_message, from_number, transcript)
    return {"status": "processing", "transcript": transcript}

@app.get("/api/claims")
async def get_claims():
    db: Session = SessionLocal()
    try:
        checks = db.query(FactCheck).order_by(FactCheck.timestamp.desc()).all()
        return checks
    finally:
        db.close()

@app.post("/api/claims/{claim_id}/flag")
async def flag_claim(claim_id: int):
    db: Session = SessionLocal()
    try:
        check = db.query(FactCheck).filter(FactCheck.id == claim_id).first()
        if not check:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Toggle flag
        check.flagged_by_ngo = 1 if check.flagged_by_ngo == 0 else 0
        db.commit()
        return {"status": "success", "flagged": check.flagged_by_ngo}
    finally:
        db.close()

@app.get("/api/analytics")
async def get_analytics():
    db: Session = SessionLocal()
    try:
        total = db.query(FactCheck).count()
        true_claims = db.query(FactCheck).filter(FactCheck.verdict == "True").count()
        false_claims = db.query(FactCheck).filter(FactCheck.verdict == "False").count()
        misleading_claims = db.query(FactCheck).filter(FactCheck.verdict == "Misleading").count()
        
        # Calculate score distribution for charts
        score_distribution = [0] * 10
        all_checks = db.query(FactCheck).all()
        for check in all_checks:
            if check.virality_score and 1 <= check.virality_score <= 10:
                score_distribution[check.virality_score - 1] += 1
                
        return {
            "total": total,
            "true": true_claims,
            "false": false_claims,
            "misleading": misleading_claims,
            "trending_language": "Tamil",
            "score_distribution": score_distribution
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
