from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
import uvicorn
import os
import json
import asyncio
import traceback
from dotenv import load_dotenv

# MUST load dot_env before importing services that rely on API keys
load_dotenv()

# ── Startup Validation ──────────────────────────────────────────────
def _check_env():
    """Print clear warnings at startup for missing env vars."""
    required = {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
    }
    optional = {
        "WHATSAPP_TOKEN": os.getenv("WHATSAPP_TOKEN"),
        "WHATSAPP_PHONE_NUMBER_ID": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        "FASTAPI_VERIFY_TOKEN": os.getenv("FASTAPI_VERIFY_TOKEN"),
    }
    
    all_ok = True
    for name, val in required.items():
        if not val:
            print(f"[CRITICAL] Missing required env var: {name}")
            all_ok = False
        else:
            print(f"[OK] {name} = {val[:8]}...")
    
    for name, val in optional.items():
        if not val:
            print(f"[WARN] Missing optional env var: {name} (WhatsApp features disabled)")
        else:
            print(f"[OK] {name} = {val[:8]}...")
    
    return all_ok

_check_env()

from services.whatsapp_handler import send_whatsapp_message, download_whatsapp_media
from services.transcription import transcribe_audio
from services.fact_checker import extract_claims, search_facts, generate_verdict

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WhatsApp Fact-Checker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],  # Allow frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from sqlalchemy.orm import Session
from db.database import SessionLocal, init_db
from models.fact_check import FactCheck

# Initialize database
try:
    init_db()
    print("[OK] Database initialized")
except Exception as e:
    print(f"[ERROR] DB Init error: {e}")
    traceback.print_exc()

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
        print(f"[PIPELINE] Extracting claims from: {text[:80]}...")
        claim = await extract_claims(text)
        print(f"[PIPELINE] Claim: {claim[:80]}...")
        
        search_results = await search_facts(claim)
        print(f"[PIPELINE] Got {len(search_results.get('organic', []))} search results")
        
        verdict_json = await generate_verdict(claim, search_results, language)
        verdict = json.loads(verdict_json)
        print(f"[PIPELINE] Verdict: {verdict.get('Verdict')} (Confidence: {verdict.get('Confidence Level')}%)")
        
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
        print(f"[OK] Saved fact-check #{new_check.id} to database")
        
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
        print(f"[ERROR] Fact-checking pipeline failed: {e}")
        traceback.print_exc()
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
        print(f"[ERROR] Media processing failed: {e}")
        traceback.print_exc()
        await send_whatsapp_message(from_number, "An error occurred during media processing.")

async def process_text_message(from_number: str, text: str):
    await send_whatsapp_message(from_number, "Analyzing your text claim... 🕒")
    await perform_fact_check_and_save(from_number, text, "text_msg", "Text")

@app.get("/")
async def root():
    return {"message": "WhatsApp Fact-Checker API is running", "status": "healthy"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    hub_mode = request.query_params.get("hub.mode")
    hub_token = request.query_params.get("hub.verify_token")
    hub_challenge = request.query_params.get("hub.challenge")
    
    verify_token = os.getenv("FASTAPI_VERIFY_TOKEN", "factcheck_token")
    
    print(f"[WEBHOOK] Verification attempt: mode={hub_mode}, token_match={hub_token == verify_token}")
    
    if hub_mode == "subscribe" and hub_token == verify_token:
        print(f"[OK] Webhook verified! Challenge: {hub_challenge}")
        return Response(content=hub_challenge, media_type="text/plain")
    
    print(f"[ERROR] Webhook verification failed!")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def handle_whatsapp_message(request: Request):
    data = await request.json()
    
    try:
        # WhatsApp Cloud API structure
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return {"status": "no message"}
        
        message = messages[0]
        from_number = message.get("from")
        msg_type = message.get("type")
        
        print(f"[WEBHOOK] Received {msg_type} message from {from_number}")
        
        if msg_type in ["audio", "voice"]:
            media_id = message.get(msg_type, {}).get("id")
            # Use asyncio.create_task for proper async execution
            asyncio.create_task(process_media_message(from_number, media_id, msg_type))
        
        elif msg_type == "image":
            media_id = message.get("image", {}).get("id")
            caption = message.get("image", {}).get("caption", "")
            asyncio.create_task(process_media_message(from_number, media_id, "image", caption))
        
        elif msg_type == "text":
            text = message.get("text", {}).get("body")
            asyncio.create_task(process_text_message(from_number, text))
            
    except Exception as e:
        print(f"[ERROR] Webhook handler error: {e}")
        traceback.print_exc()
    
    return {"status": "received"}

@app.post("/api/process_audio")
async def process_audio_endpoint(request: Request):
    """Simulate processing a text claim (used by the dashboard simulator)."""
    data = await request.json()
    transcript = data.get("text")
    if not transcript:
        raise HTTPException(status_code=400, detail="Missing text in simulation payload")
        
    # Generate a dummy media_id and from_number for the simulator
    media_id = "simulated_" + transcript[:10]
    from_number = "Simulator_User"
    
    print(f"[SIMULATOR] Processing claim: {transcript[:80]}...")
    
    # Use asyncio.create_task for proper async execution
    asyncio.create_task(process_text_message(from_number, transcript))
    return {"status": "processing", "transcript": transcript}

@app.get("/api/claims")
async def get_claims():
    db: Session = SessionLocal()
    try:
        checks = db.query(FactCheck).order_by(FactCheck.timestamp.desc()).all()
        return checks
    except Exception as e:
        print(f"[ERROR] get_claims: {e}")
        return []
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
        
        # Find the most common language
        from sqlalchemy import func
        top_lang = db.query(FactCheck.language, func.count(FactCheck.language).label('cnt')).group_by(FactCheck.language).order_by(func.count(FactCheck.language).desc()).first()
        trending_language = top_lang[0] if top_lang else "N/A"
                
        return {
            "total": total,
            "true": true_claims,
            "false": false_claims,
            "misleading": misleading_claims,
            "trending_language": trending_language,
            "score_distribution": score_distribution
        }
    except Exception as e:
        print(f"[ERROR] get_analytics: {e}")
        return {
            "total": 0, "true": 0, "false": 0, "misleading": 0,
            "trending_language": "N/A", "score_distribution": [0]*10
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
