import whisper
import os

# Load model lazily to save memory during startup
_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model

async def transcribe_audio(file_path: str):
    model = get_model()
    result = model.transcribe(file_path)
    # Clean up temp file
    if os.path.exists(file_path):
        os.remove(file_path)
    return result["text"], result.get("language", "unknown")
