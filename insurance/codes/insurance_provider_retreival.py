import numpy as np
import pandas as pd
import os
import csv
import re
from dotenv import load_dotenv
import json
from openai import OpenAI

path = '/home/cptaswadu/RESCUE-n8n/insurance'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
client = OpenAI(api_key=openai_api_key)

ROOT_DIR = "/home/cptaswadu/RESCUE-n8n/insurance"
PROVIDERS_EVAL_DIR = os.path.join(ROOT_DIR, "results/providers_generation_eval_results")

df = pd.read_csv('/home/cptaswadu/RESCUE-n8n/insurance/In-Network_providers.csv')
real_list = df["In-network Provider"].dropna().str.strip().tolist()

def normalize_provider(name): #add annotation
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

def evaluate_llm_provider_performance(messages, ground_truth_list, prompt_name=None, experiment_id=None, output_dir=PROVIDERS_EVAL_DIR):
    """
    Evaluate the LLM-generated list of in-network providers against a ground truth list.
    Saves evaluation results and handles error cases such as invalid JSON responses.

    Parameters:
    - messages: list of dicts (Chat API message format)
    - ground_truth_list: list of strings (manually verified provider names)
    - prompt_name: str, identifier for the prompt used
    - experiment_id: int or str, identifier for the experiment repetition
    - output_dir: str, directory to save evaluation results

    Returns:
    - Dictionary containing evaluation summary (precision, recall, etc.)
    """

    def try_llm_response_with_retry(message_block, max_retries=3):
        """
        Retry LLM API call up to max_retries times.
        """
        for attempt in range(1, max_retries + 1):
            try:
                print(f"🔁 Attempt {attempt} to get LLM response...")
                response = client.responses.create(
                    model="gpt-4o",
                    tools=[{"type": "web_search_preview"}],
                    input=message_block
                )
                return response.output_text.strip()
            except Exception as e:
                print(f"❌ Attempt {attempt} failed: {e}")
        return None

    # 1. Query LLM
    response_text = try_llm_response_with_retry(messages)
    if not response_text:
        return {
            "error": "All attempts failed.",
            "Precision (%)": 0,
            "Recall (%)": 0
        }

    # 2. Preprocess and patch invalid JSON edge cases
    response_text = re.sub(r"^```json\s*", "", response_text)
    response_text = re.sub(r"\s*```$", "", response_text)

    if response_text.endswith(","):
        response_text = response_text.rstrip(",") + "]}"

    elif response_text.endswith("["):
        response_text += "]}"

    elif "Providers" in response_text and "source_url" not in response_text:
        response_text += ', "source_url": ""}'

    # 3. Attempt to parse JSON
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        print("❌ JSON decoding failed even after retry.")
        print(response_text[:500])

        os.makedirs(output_dir, exist_ok=True)
        fail_path = os.path.join(output_dir, f"{prompt_name}_experiment{experiment_id}_failed.csv")
        pd.DataFrame([{"error": "invalid JSON", "raw_output": response_text}]).to_csv(fail_path, index=False)
        print(f"⚠️ Raw output saved to '{fail_path}'")

        return {
            "error": "invalid JSON",
            "Precision (%)": 0,
            "Recall (%)": 0
        }

    # 4. Normalize and compare providers
    llm_raw_list = result.get("Providers", [])
    llm_normalized_list = [normalize_provider(name) for name in llm_raw_list]

    ground_truth_set = set(ground_truth_list)
    llm_set = set(llm_normalized_list)

    common = ground_truth_set & llm_set
    missing = ground_truth_set - llm_set
    extra = llm_set - ground_truth_set

    precision = len(common) / len(llm_set) * 100 if llm_set else 0
    recall = len(common) / len(ground_truth_set) * 100 if ground_truth_set else 0

    evaluation_result = {
        "prompt_name": prompt_name,
        "experiment_id": experiment_id,
        "ground_truth_count": len(ground_truth_list),
        "llm_returned_count": len(llm_set),
        "common_count": len(common),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "Precision (%)": round(precision, 2),
        "Recall (%)": round(recall, 2)
    }

    # 5. Save results to CSV
    if prompt_name and experiment_id is not None:
        os.makedirs(output_dir, exist_ok=True)
        eval_path = os.path.join(output_dir, f"{prompt_name}_experiment{experiment_id}.csv")
        pd.DataFrame([evaluation_result]).to_csv(eval_path, index=False)
        print(f"📁 Evaluation result saved to '{eval_path}'")

    return evaluation_result

def provider_task_prompt_baseline():
    '''
    The first basic prompt
    '''
    return [
        {
            "role": "system",
            "content": "You are a helpful assistant. Respond only in strict JSON format with no explanation or extra commentary."
        },
        {
            "role": "user",
            "content": (
                "List all the medical insurance providers that are currently in-network with GeneDx. "
                "Format your response as: "
                "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
                "Only use information from official GeneDx or trusted affiliate websites."
            )
        }
    ]


def provider_task_prompt_counted_311():
    '''
    The second prompt with a specific request for 311 providers
    '''
    return [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            )
        },
        {
            "role": "user",
            "content": (
                "List all the 311 medical insurance providers that are currently in-network with GeneDx. "
                "Output the result strictly in JSON format using the following structure: "
                "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
                "Only include links from the official GeneDx website or affiliated trusted sources. "
                "Do not include any introduction, explanation, or extra commentary — only return the JSON object."
            )
        }
    ]

def provider_task_prompt_explicit_source():
    '''
    The third prompt with an explicit source
    '''
    return [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            )
        },
        {
            "role": "user",
            "content": (
                "List all the medical insurance providers that are currently in-network with GeneDx. "
                "You may use the official GeneDx insurance network page at "
                "https://www.genedx.com/commercial-insurance-in-network-contracts/ as the primary source of information. "
                "Output the result strictly in JSON format using the following structure: "
                "{\"Providers\": [list of provider names], \"source_url\": \"link to the official source\"}. "
                "Only include links from the official GeneDx website or affiliated trusted sources. "
                "Do not include any introduction, explanation, or extra commentary — only return the JSON object."
            )
        }
    ]


prompt_bank = {
    "baseline": provider_task_prompt_baseline,
    "counted_311": provider_task_prompt_counted_311,
    "explicit_source": provider_task_prompt_explicit_source,
}

def summarize_eval_results(evaluation_df, output_path=os.path.join(PROVIDERS_EVAL_DIR, "summary_stats.csv")):
    if evaluation_df.empty:
        print("⚠️ No data to summarize.")
        return

    group_cols = ["prompt_name"]
    metric_cols = ["Precision (%)", "Recall (%)", "ground_truth_count", "llm_returned_count", "common_count", "missing_count", "extra_count"]

    # Compute mean and std
    summary = evaluation_df.groupby(group_cols)[metric_cols].agg(['mean', 'std']).round(2)
    summary.columns = ['_'.join(col) for col in summary.columns]
    summary.reset_index(inplace=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary.to_csv(output_path, index=False)
    print(f"📊 Summary statistics saved to '{output_path}'")

    return summary

### just in case making multiple runs
def run_all_prompt_evaluations(real_list, prompt_bank, num_experiments=1, output_dir=PROVIDERS_EVAL_DIR):
    """
    Executes LLM evaluations for all prompts and multiple experiment runs.

    Args:
        real_list (list): Ground truth list of providers.
        prompt_bank (dict): Dictionary mapping prompt names to prompt-generating functions.
        num_experiments (int): Number of times each prompt is evaluated.
        output_dir (str): Directory to save evaluation results.

    Returns:
        pd.DataFrame: Combined evaluation results from all runs.
    """
    all_results = []

    for prompt_name, prompt_fn in prompt_bank.items():
        for exp_id in range(1, num_experiments + 1):
            print(f"\n🚀 Running {prompt_name}, Experiment {exp_id}")
            messages = prompt_fn()
            result = evaluate_llm_provider_performance(
                messages=messages,
                ground_truth_list=real_list,
                prompt_name=prompt_name,
                experiment_id=exp_id,
                output_dir=output_dir
            )
            all_results.append(result)

    # Convert to DataFrame and save combined results
    df = pd.DataFrame(all_results)
    summary_path = os.path.join(output_dir, "combined_evaluation_summary.csv")
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(summary_path, index=False)
    print(f"\n📊 Combined evaluation summary saved to '{summary_path}'")
    return df

if __name__ == "__main__":
    print("🚀 Starting provider evaluation...")

    df = run_all_prompt_evaluations(
        real_list=real_list,
        prompt_bank=prompt_bank,
        num_experiments=3
    )

    # Add stats summary
    summarize_eval_results(df)