import numpy as np
import pandas as pd
import os
import csv
import re
from dotenv import load_dotenv
import json
from openai import OpenAI
import requests

# Load environment variables
path = '/home/cptaswadu/RESCUE-n8n/insurance'
load_dotenv(dotenv_path=os.path.join(path, '.env')) 
openai_api_key = os.getenv("OPEN_AI_API_KEY")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
gpt_client = OpenAI(api_key=openai_api_key)

# Directories
ROOT_DIR = "/home/cptaswadu/RESCUE-n8n/insurance"
RESULT_DIR = os.path.join(ROOT_DIR, "results/Providers Retrieval")

# Number of times to repeat each experiment
N_EXPERIMENTS = 3

# List of LLM models to evaluate
MODELS = ["ChatGPT", "perplexity"]

# Manually verified list of in-network providers
df = pd.read_csv('/home/cptaswadu/RESCUE-n8n/insurance/In-Network_providers.csv')
real_list = df["In-network Provider"].dropna().str.strip().tolist()

# prompts
def make_prompt(system_message, user_message):
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]

PROMPT_TEMPLATES = {
    "baseline": (
        "You are a helpful assistant. Respond only in strict JSON format with no explanation or extra commentary.",
        "List all the medical insurance providers that are currently in-network with GeneDx. "
        "Format your response as: "
        "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
        "Only use information from official GeneDx or trusted affiliate websites."
    ),
    "counted_311": (
        "You are an artificial intelligence assistant and you need to "
        "engage in a helpful, detailed, polite conversation with a user.",
        "List all the 311 medical insurance providers that are currently in-network with GeneDx. "
        "Output the result strictly in JSON format using the following structure: "
        "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
        "Only include links from the official GeneDx website or affiliated trusted sources. "
        "Do not include any introduction, explanation, or extra commentary — only return the JSON object."
    ),
    "explicit_source": (
        "You are an artificial intelligence assistant and you need to "
        "engage in a helpful, detailed, polite conversation with a user.",
        "List all the medical insurance providers that are currently in-network with GeneDx. "
        "You may use the official GeneDx insurance network page at "
        "https://www.genedx.com/commercial-insurance-in-network-contracts/ as the primary source of information. "
        "Output the result strictly in JSON format using the following structure: "
        "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
        "Only include links from the official GeneDx website or affiliated trusted sources. "
        "Do not include any introduction, explanation, or extra commentary — only return the JSON object."
    )
}

prompt_bank = {key: lambda sm=sm, um=um: make_prompt(sm, um) for key, (sm, um) in PROMPT_TEMPLATES.items()}


def normalize_provider_name(name):
    '''
    Normalize the provider name by removing unnecessary parts and standardizing the format.
    1. Kansas City -> Kansas
    2. State Medicaid (FFS) -> State Medicaid
    3. Blue Shield of -> BS
    '''
    name = name.strip()

    if "Kansas City" in name:
        name = name.replace("Kansas City", "Kansas")

    if name.endswith("(FFS)"):
        name = name.replace("(FFS)", "").strip()

    if "Blue Shield of" in name:
        name = name.replace("Blue Shield of", "BS")

    return name

# Function for pPerplexity API
def query_perplexity(messages, api_key, model="sonar-pro"):
    """
    Call Perplexity API using raw HTTP request via requests.post.
    
    Args:
        messages (list): List of chat messages (role-content format).
        api_key (str): Perplexity API key.
        model (str): Model name. Default is "pplx-70b-chat".

    Returns:
        str: Response text (LLM output only).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": model,
        "messages": messages
    }

    url = "https://api.perplexity.ai/chat/completions"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    
    except requests.exceptions.RequestException as e:
        print(f"❗ Perplexity API call failed: {e}")
        return None

# Experiment function
def query_llm_for_providers(messages, model="ChatGPT", openai_client=None, perplexity_api_key=None, max_retries=3):
    def call_ChatGPT():
        response = gpt_client.responses.create(
            model="gpt-4o",
            input=messages,
            tools=[{"type": "web_search_preview"}],
            temperature=0
        )

        result = response.output_text.strip()
        print("✅ ChatGPT Response:\n", result)
        return result

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
            result = res.json()["choices"][0]["message"]["content"].strip()
            print("✅ Perplexity Response:\n", result)
            return result
        else:
            raise Exception(f"Perplexity error: {res.status_code} - {res.text}")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔁 Attempt {attempt} ({model})...")
            return call_perplexity() if model == "perplexity" else call_ChatGPT()
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
    return None


# Extranct LLM response in JSON format
def extract_provider_json(response_text):
    """
    Attempts to extract a valid JSON object containing 'Providers' and 'source_url' fields
    from possibly malformed, long, or incomplete LLM responses.
    """
    original = response_text.strip()

    # Step 1: Try to extract ```json ... ``` or ``` blocks
    json_block = re.search(r"```(?:json)?\s*(\{[\s\S]+?)```", original, re.IGNORECASE)
    if json_block:
        candidate = json_block.group(1).strip()
    else:
        # Step 2: Fallback: find first "{" block
        brace_match = re.search(r"(\{[\s\S]+)", original)
        candidate = brace_match.group(1).strip() if brace_match else original

    # Step 3: Try direct JSON parsing
    try:
        result = json.loads(candidate)
        if isinstance(result, dict) and "Providers" in result:
            result["Providers"] = list(set(result.get("Providers", [])))  # Deduplicate
            return result
    except json.JSONDecodeError:
        pass

    # Step 4: Manual recovery of "Providers" list from malformed text
    provider_list_match = re.search(r'"Providers"\s*:\s*\[([\s\S]+?)\](,|\s*\})', candidate)
    if provider_list_match:
        raw_items = provider_list_match.group(1)
        providers = re.findall(r'"(.*?)"', raw_items)
        return {
            "Providers": list(set(providers)),  # Deduplicated list
            "source_url": ""
        }

    print("⚠️ Could not parse JSON. Using fallback empty provider list.")
    return {
        "Providers": [],
        "source_url": ""
    }




# Evaluation function
def compute_provider_metrics(predicted, ground_truth):
    """
    Compute precision and recall between predicted and ground truth provider lists.
    Handles empty input cases safely.
    """
    # If either list is empty, return zeros and diagnostics
    if not predicted or not ground_truth:
        return {
            "ground_truth_count": len(ground_truth),
            "llm_returned_count": len(predicted),
            "common_count": 0,
            "missing_count": len(ground_truth),
            "extra_count": len(predicted),
            "Precision (%)": 0.0,
            "Recall (%)": 0.0,
        }

    pred_set = set(normalize_provider_name(x) for x in predicted)
    gt_set = set(normalize_provider_name(x) for x in ground_truth)
    common = pred_set & gt_set
    precision = len(common) / len(pred_set) * 100 if pred_set else 0
    recall = len(common) / len(gt_set) * 100 if gt_set else 0

    return {
        "ground_truth_count": len(gt_set),
        "llm_returned_count": len(pred_set),
        "common_count": len(common),
        "missing_count": len(gt_set - pred_set),
        "extra_count": len(pred_set - gt_set),
        "Precision (%)": round(precision, 2),
        "Recall (%)": round(recall, 2),
    }

# Trnsform the result to a DataFrame & save it
def export_evaluation_to_csv(result, model, prompt_name, experiment_id, output_dir):
    if prompt_name and experiment_id is not None:
        trial_dir = os.path.join(output_dir, f"{model}_{prompt_name}_experiment{experiment_id}")
        os.makedirs(trial_dir, exist_ok=True)
        path = os.path.join(trial_dir, "evaluation.csv")
        df = pd.DataFrame([result])
        print(df)
        df.to_csv(path, index=False)
        print(f"✅ Saved: {path}")

# Main function to run all experiments
def run_all_experiments():
    provider_csv_root = RESULT_DIR

    for experiment_id in range(1, N_EXPERIMENTS + 1):
        print(f"\n🚀 Starting Experiment {experiment_id}...\n")

        for model in MODELS:
            for prompt_name, prompt_fn in prompt_bank.items():
                print(f"=== {model.upper()} - Prompt: {prompt_name} ===")

                messages = prompt_fn()
                response_text = query_llm_for_providers(
                    messages=messages,
                    model=model,
                    openai_client=gpt_client,
                    perplexity_api_key=perplexity_api_key
                )

                if response_text:
                    try:
                        parsed = extract_provider_json(response_text)
                        providers = parsed.get("Providers", [])
                        df_providers = pd.DataFrame(providers, columns=["Providers"])

                        # ✅ Save provider.csv under results/provider_retrieval
                        trial_folder = os.path.join(provider_csv_root, f"{model}_{prompt_name}_experiment{experiment_id}")
                        os.makedirs(trial_folder, exist_ok=True)
                        df_providers.to_csv(os.path.join(trial_folder, "provider.csv"), index=False)

                        # ✅ Save evaluation summary to RESULT_DIR
                        result = compute_provider_metrics(providers, real_list)
                        export_evaluation_to_csv(result, model, prompt_name, experiment_id, RESULT_DIR)

                    except Exception as e:
                        print(f"⚠️ Error during parsing or saving: {e}")
                else:
                    print("⚠️ No valid response from model")
if __name__ == "__main__":
    run_all_experiments()