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
    Return only the claim text. If no factual claim is found, return "No factual claim detected".
    """
    response = model.generate_content(prompt)
    return response.text.strip()

async def search_facts(claim: str):
    if claim == "No factual claim detected":
        return {"organic": []}
        
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
    Return only the claim text. If no factual claim is found, return "No factual claim detected".
    """
    
    response = model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": image_data}
    ])
    
    # Clean up temp file
    if os.path.exists(image_path):
        os.remove(image_path)
        
    return response.text.strip()

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
    
    context = "\n---\n".join(snippets)

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
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Robust JSON cleaning
        if "```" in text:
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
            
        # Try parsing to validate it before returning
        import json
        json.loads(text) 
        return text
    except Exception as e:
        print(f"Error parsing Gemini JSON: {e}")
        import json
        return json.dumps({
            "Verdict": "Unverified",
            "Confidence Level": 0,
            "Explanation": f"Error generating automated verdict: {str(e)}",
            "Virality Risk Score": 5,
            "Counter Message": ""
        })
