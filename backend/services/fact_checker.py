import google.generativeai as genai
import os
import json
import re
import httpx
import traceback
import time

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Model fallback chain — if one model hits rate limits, try the next
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
                    print(f"[WARN] {model_name} quota exhausted (attempt {attempt+1}), trying next...")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Brief pause before retry
                    break  # Move to next model
                else:
                    print(f"[ERROR] {model_name} error: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                    else:
                        raise  # Non-quota errors should propagate
    
    raise last_error  # If all models failed

async def extract_claims(text: str):
    prompt = f"""
    Extract the main factual claim from the following transcribed text. 
    If there are multiple, focus on the most viral/misleading one.
    Text: {text}
    Return only the claim text. If no factual claim is found, return "No factual claim detected".
    """
    try:
        response = _generate_with_fallback(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] extract_claims failed: {e}")
        traceback.print_exc()
        return text  # Fallback: use raw text as the claim

async def search_facts(claim: str):
    if claim == "No factual claim detected":
        return {"organic": []}
        
    url = "https://google.serper.dev/search"
    payload = {"q": claim}
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            return response.json()
    except Exception as e:
        print(f"[ERROR] search_facts failed: {e}")
        traceback.print_exc()
        return {"organic": []}

async def extract_claims_from_image(image_path: str, caption: str):
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        prompt = f"""
        Analyze this image and its caption: "{caption}".
        Extract any factual claims being made in the image text or context.
        If the image contains a viral message or news, identify the core claim.
        Return only the claim text. If no factual claim is found, return "No factual claim detected".
        """
        
        response = _generate_with_fallback([
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ])
        
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] extract_claims_from_image failed: {e}")
        traceback.print_exc()
        return "No factual claim detected"
    finally:
        # Clean up temp file
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except:
                pass

async def generate_verdict(claim: str, search_results: dict, language: str):
    if claim == "No factual claim detected":
        return json.dumps({
            "Verdict": "N/A",
            "Confidence Level": 100,
            "Explanation": "No factual claim was found in the message.",
            "Virality Risk Score": 1,
            "Counter Message": ""
        })

    # Keep only snippet and title from search results to stay within context limits
    snippets = []
    for result in search_results.get("organic", [])[:5]:
        snippets.append(f"Title: {result.get('title')}\nSnippet: {result.get('snippet')}")
    
    context = "\n---\n".join(snippets) if snippets else "No search results found."

    prompt = f"""
    Analyze the following claim against the provided search results and provide a verdict.
    
    Claim: {claim}
    
    Search Results:
    {context}
    
    Instructions:
    1. Verdict: Must be one of [True, False, Misleading, Unverified].
    2. Confidence Level: Numeric score from 0 to 100.
    3. Explanation: Detailed reasoning for the verdict, written in {language}.
    4. Virality Risk Score: Scale of 1 to 10 (High means very likely to spread as harmful misinformation).
    5. Counter Message: A short, persuasive, and friendly WhatsApp response (with emojis) to debunk the claim if it's False or Misleading. Write this in {language}.
    
    Important: Return ONLY a valid JSON object. Do not include markdown formatting or extra text.
    Example:
    {{"Verdict": "False", "Confidence Level": 95, "Explanation": "Reasoning in {language}...", "Virality Risk Score": 8, "Counter Message": "Correction in {language}..."}}
    """
    
    try:
        response = _generate_with_fallback(prompt)
        text = response.text.strip()
        
        # Robust JSON cleaning
        if "```" in text:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
        # Try parsing to validate it before returning
        json.loads(text) 
        return text
    except Exception as e:
        print(f"[ERROR] generate_verdict failed: {e}")
        traceback.print_exc()
        return json.dumps({
            "Verdict": "Unverified",
            "Confidence Level": 0,
            "Explanation": f"Error generating automated verdict: {str(e)}",
            "Virality Risk Score": 5,
            "Counter Message": ""
        })
