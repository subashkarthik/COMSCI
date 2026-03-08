import google.generativeai as genai
import os
import httpx

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

async def extract_claims(text: str):
    prompt = f"""
    Extract the main factual claim from the following transcribed text. 
    If there are multiple, focus on the most viral/misleading one.
    Text: {text}
    Return only the claim text.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

async def search_facts(claim: str):
    url = "https://google.serper.dev/search"
    payload = {"q": claim}
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        return response.json()

async def extract_claims_from_image(image_path: str, caption: str):
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    prompt = f"""
    Analyze this image and its caption: "{caption}".
    Extract any factual claims being made in the image text or context.
    If the image contains a viral message or news, identify the core claim.
    Return only the claim text.
    """
    
    response = model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": image_data}
    ])
    return response.text.strip()

async def generate_verdict(claim: str, search_results: dict, language: str):
    prompt = f"""
    Analyze the following claim against the search results and provide a verdict.
    Claim: {claim}
    Search Results: {search_results}
    
    Provide:
    1. Verdict (True, False, Misleading, Unverified)
    2. Confidence Level (0-100)
    3. Explanation in {language}
    4. Virality Risk Score (1-10)
    5. Counter Message: A short, WhatsApp-friendly text (with emojis) to reply to the user correcting the misinformation (in {language}). If the verdict is True, this can be empty.
    
    Return ONLY a valid JSON object. Do not wrap it in markdown. Example:
    {{"Verdict": "False", "Confidence Level": 95, "Explanation": "...", "Virality Risk Score": 8, "Counter Message": "..."}}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up JSON if LLM adds markdown backticks
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
            
        # Try parsing to validate it before returning
        import json
        json.loads(text) # If this fails, it goes to except
        return text
    except Exception as e:
        print(f"Error parsing Gemini JSON: {e}")
        # Return a safe fallback JSON
        import json
        return json.dumps({
            "Verdict": "Unverified",
            "Confidence Level": 0,
            "Explanation": f"Error generating automated verdict: {str(e)}",
            "Virality Risk Score": 5,
            "Counter Message": ""
        })
