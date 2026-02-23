import os
import json
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv
from prompt import prompt_functions

def clean_json_response(response_text):
    original = response_text.strip()
    
    try:
        result = json.loads(original)
        if isinstance(result, dict) and "Providers" in result:
            return result
    except json.JSONDecodeError:
        pass
    
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", original, flags=re.IGNORECASE).strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict) and "Providers" in result:
            return result
    except json.JSONDecodeError:
        pass
    
    match = re.search(r"(\{[\s\S]*?\})", original)
    if match:
        try:
            result = json.loads(match.group(1))
            if isinstance(result, dict) and "Providers" in result:
                return result
        except json.JSONDecodeError:
            pass
    
    return {
        "Providers": [],
        "source_url": ""
    }


def query_llm_for_providers(prompt_type="baseline", model="openai", 
                             openai_model="gpt-4o", iteration=1, base_output_dir="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval",
                             openai_client=None, perplexity_api_key=None, max_retries=3):
    
    prompt_text = prompt_functions[prompt_type]()
    messages = [{"role": "user", "content": prompt_text}]
    
    actual_model = openai_model if model == "openai" else "perplexity"
    output_folder = os.path.join(
        base_output_dir, 
        f"iteration_{iteration}", 
        actual_model, 
        prompt_type
    )
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
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt} ({actual_model})")
            
            raw_response = call_perplexity() if model == "perplexity" else call_openai()
            parsed_result = clean_json_response(raw_response)
            
            with open(os.path.join(output_folder, "raw_response.txt"), "w", encoding="utf-8") as f:
                f.write(raw_response)
            
            result = {
                "prompt_type": prompt_type,
                "model": actual_model,
                "iteration": iteration,
                "attempt": attempt,
                "success": True,
                "raw_response": raw_response,
                "parsed_data": parsed_result
            }
            
            with open(os.path.join(output_folder, "result.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            return result
            
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
    
    return None

if __name__ == "__main__":
    base_output_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval/example"
    os.makedirs(base_output_dir, exist_ok=True)

    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    openai_client = OpenAI(api_key=openai_api_key)
    
    result = query_llm_for_providers(
        prompt_type="baseline",
        model="openai",
        openai_model="gpt-5-mini",
        iteration=1,
        base_output_dir=base_output_dir,
        openai_client=openai_client,
        perplexity_api_key=perplexity_api_key,
        max_retries=3
    )
    
    print("Final Result:", result)