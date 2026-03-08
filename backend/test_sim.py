import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

from services.fact_checker import extract_claims, search_facts, generate_verdict
from services.fact_checker import extract_claims, search_facts, generate_verdict

async def run():
    text = "drinking hot water cures covid"
    language = "English"
    
    print("1. Extracting Claims")
    claim = await extract_claims(text)
    print(f"Claim: {claim}")
    
    print("2. Searching Facts")
    search_results = await search_facts(claim)
    print("Search Results found.")
    
    print("3. Generating Verdict")
    verdict_json = await generate_verdict(claim, search_results, language)
    print(f"Raw Verdict JSON: {verdict_json}")
    
    verdict = json.loads(verdict_json)
    print("Parsed Verdict:", verdict)
    
if __name__ == "__main__":
    asyncio.run(run())
