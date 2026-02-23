import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
from prompt import prompt_functions

def clean_json_response(response_text):
    """Return a parsed JSON object from an LLM response, stripping code fences and extra text."""
    # Clean and extract JSON from the response text
    original = response_text.strip()

    # Step 0: Check for hallucinated greeting (Perplexity fallback)
    if "how can I assist you" in original.lower() or "insurance-related questions" in original.lower():
        print("Warning: Detected generic response, continuing to parse")

    # Step 1: Try direct parsing
    try:
        result = json.loads(original)
        if isinstance(result, dict) and "pdf_links" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Step 2: Remove code block wrappers
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", original, flags=re.IGNORECASE).strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict) and "pdf_links" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Step 3: Try to extract the first {...} JSON-like block
    match = re.search(r"(\{[\s\S]*?\})", original)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict) and "pdf_links" in result:
                return result
        except json.JSONDecodeError:
            pass

    print("Could not parse JSON. Using fallback empty payer list")
    return {
        "pdf_links": [],
        "webpage_links": []
    }

def query_llm_for_payers(payer_name, prompt_type="baseline", model="openai", openai_model = 'gpt-4o',
                           iteration=1, base_output_dir="results",
                           openai_client=None, perplexity_api_key=None, max_retries=3):
    
    # Generate prompt and messages
    prompt_text = prompt_functions[prompt_type](payer_name)
    messages = [{"role": "user", "content": prompt_text}]
    
    # Create output folders
    actual_model = openai_model if model == "openai" else "perplexity"
    output_folder = os.path.join(base_output_dir, f"iteration_{iteration}", actual_model, prompt_type, payer_name.replace(" ", "_"))
    os.makedirs(output_folder, exist_ok=True)
    
    def call_openai():
        response = openai_client.responses.create(
            model=openai_model,
            input=messages,
            tools=[{"type": "web_search"}]
        )
        return response.output_text.strip()

    def call_perplexity():
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "sonar-pro",
            "messages": messages
        }
        url = "https://api.perplexity.ai/chat/completions"
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(f"Perplexity error: {res.status_code} - {res.text}")

    # Try API calls with retry
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt} ({actual_model})...")
            raw_response = call_perplexity() if model == "perplexity" else call_openai()
            parsed_result = clean_json_response(raw_response)
            
            # Save raw response
            with open(os.path.join(output_folder, f"{payer_name}_raw_response.txt"), "w") as f:
                f.write(raw_response)
            
            # Save experiment result
            result = {
                "payer": payer_name,
                "prompt_type": prompt_type,
                "model": model,
                "iteration": iteration,
                "attempt": attempt,
                "success": True,
                "raw_response": raw_response,
                "parsed_data": parsed_result
            }
            
            with open(os.path.join(output_folder, f"{payer_name}_result.json"), "w") as f:
                json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
    
    return None

if __name__ == "__main__":
    base_output_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/payer_retrieval/example"
    os.makedirs(base_output_dir, exist_ok=True)

    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)

    result_ex = query_llm_for_payers(
        payer_name="United Healthcare",
        prompt_type="verified",
        model="openai",
        openai_model='gpt-5-mini',
        iteration=1,
        base_output_dir=base_output_dir,
        openai_client=chatgpt_agent,
        perplexity_api_key=perplexity_api_key,
        max_retries=3
    )