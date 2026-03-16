import os
import traceback
import time
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Use Gemini for audio transcription instead of openai-whisper
genai.configure(api_key=GEMINI_API_KEY)

# Model fallback chain for transcription
MODEL_CHAIN = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']
_models = {name: genai.GenerativeModel(name) for name in MODEL_CHAIN}

def _generate_with_fallback(content, max_retries=2):
    """Try generating content with model fallback chain and retry logic."""
    last_error = None
    for model_name in MODEL_CHAIN:
        model = _models[model_name]
        for attempt in range(max_retries):
            try:
                response = model.generate_content(content)
                return response
            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                    print(f"[WARN] Transcription: {model_name} quota hit (attempt {attempt+1}), trying next...")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    break
                else:
                    print(f"[ERROR] Transcription: {model_name} error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        raise
    raise last_error

async def transcribe_audio(file_path: str):
    """Transcribe audio using Gemini's multimodal capabilities."""
    try:
        with open(file_path, "rb") as f:
            audio_data = f.read()
        
        # Determine MIME type based on file extension
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".ogg": "audio/ogg",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".webm": "audio/webm",
            ".opus": "audio/opus",
        }
        mime_type = mime_map.get(ext, "audio/ogg")
        
        prompt = """Transcribe this audio message accurately. 
        Also detect the language being spoken.
        Return your response in this exact format:
        TRANSCRIPT: <the transcription here>
        LANGUAGE: <detected language name>
        
        If you cannot transcribe it, return:
        TRANSCRIPT: Unable to transcribe audio
        LANGUAGE: unknown"""
        
        response = _generate_with_fallback([
            prompt,
            {"mime_type": mime_type, "data": audio_data}
        ])
        
        result_text = response.text.strip()
        
        # Parse the structured response
        transcript = result_text
        language = "unknown"
        
        if "TRANSCRIPT:" in result_text:
            parts = result_text.split("LANGUAGE:")
            transcript = parts[0].replace("TRANSCRIPT:", "").strip()
            if len(parts) > 1:
                language = parts[1].strip()
        
        print(f"[OK] Transcribed audio: {transcript[:80]}... (Language: {language})")
        return transcript, language
        
    except Exception as e:
        print(f"[ERROR] transcribe_audio failed: {e}")
        traceback.print_exc()
        return "Unable to transcribe audio", "unknown"
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
