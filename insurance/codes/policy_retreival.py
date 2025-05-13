import numpy as np
import pandas as pd
import os
import csv
import re
from dotenv import load_dotenv
import json
from openai import OpenAI
from urllib.parse import urlparse
import hashlib
import pdfkit
import requests
from playwright.sync_api import sync_playwright

path = '/home/cptaswadu/RESCUE-n8n/insurance'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
gpt_client = OpenAI(api_key=openai_api_key)

# Directories
BASE_RESULT_DIR = "/home/cptaswadu/RESCUE-n8n/insurance/results/policy_retrieval"
LLM_FOLDER_ROOT = os.path.join(BASE_RESULT_DIR, "llm_searched")
MANUAL_FOLDER = "/home/cptaswadu/RESCUE-n8n/insurance/insurance_policy"
RETRIEVAL_SUMMARY_CSV = f"{BASE_RESULT_DIR}/retrieval_summary.csv"
MD5_COMPARISON_CSV = f"{BASE_RESULT_DIR}/md5_comparison.csv"

os.makedirs(BASE_RESULT_DIR, exist_ok=True)
os.makedirs(LLM_FOLDER_ROOT, exist_ok=True)
os.makedirs(os.path.join(BASE_RESULT_DIR, "retrieval"), exist_ok=True)
os.makedirs(os.path.join(BASE_RESULT_DIR, "md5"), exist_ok=True)

# list of providers
#df = pd.read_csv('/home/cptaswadu/RESCUE-n8n/insurance/Providers_Network_update.csv')
#provider_list = df["In-network Provider"].dropna().str.strip().tolist()

def policy_retrieval_prompt_baseline(provider_name):
    """
    Retrieves all official links to genetic testing coverage policies for a provider without keyword filtering.
    Returns strictly formatted JSON with 'pdf_links' and 'webpage_links'.
    """
    return (
        f"Find and list all the links to official policy documents that contain genetic testing coverage policies "
        f"for the insurance provider '{provider_name}'. "
        "Include both PDF files and webpage URLs if the information is only available on the website. "
        "Only include links from official sources such as the insurance company's website or regulatory bodies. "
        "Exclude links from news articles, blog posts, or discussion forums. "
        "If the policy is available as a PDF, return the direct PDF link under the key \"pdf_links\". "
        "If the policy is available only as an HTML webpage, return the webpage URL under the key \"webpage_links\". "
        "The response must be strictly in JSON format with two single keys: "
        "\"pdf_links\", containing an array of valid PDF URLs, and "
        "\"webpage_links\", containing an array of valid webpage URLs. "
        "Do not include any additional text or explanations—only the JSON object."
    )

def policy_retrieval_prompt_keyword_checked_document(provider_name):
    """
    Retrieves links only if the documents contain specific genetic-related keywords and excludes irrelevant content.
    """
    return (
        f"Find and list all official links to policy documents that describe genetic testing coverage for the insurance provider '{provider_name}'. "
        "Only include documents if they contain at least one of the following key terms: "
        "'coverage policy', 'medical policy', 'clinical policy', 'WES', 'WGS', 'BRCA', 'Duchenne muscular dystrophy', "
        "'hereditary cancer', 'genetic testing', 'lynch syndrome', or 'pharmacogenetic'. "
        "Exclude any documents that contain the phrase 'providal guideline', or that are press releases, claim forms, newsletters, blog posts, or provider manuals."
        "Only include links from official sources such as the insurance company’s website or regulatory bodies. "
        "If a document is available as a downloadable PDF, return the full direct PDF link under the key 'pdf_links'. "
        "If the document is only available as a webpage, return the full URL under the key 'webpage_links'. "
        "The JSON response must follow this exact format: "
        "{\"pdf_links\": [list of direct PDF links], \"webpage_links\": [list of webpage URLs]}. "
        "If no qualifying documents are found, return empty lists. "
        "Do not include any explanation, markdown, natural language, or formatting — only return the raw JSON object."
    )

def policy_retrieval_prompt_keyword_verified_links(provider_name):
    """
    Added stricter requirements for URL validity and official policy page confirmation.
    """
    return (
        f"Find and list all official links to policy documents that describe genetic testing coverage for the insurance provider '{provider_name}'. "
        "Only include documents if they contain at least one of the following key terms: "
        "'coverage policy', 'medical policy', 'clinical policy', 'WES', 'WGS', 'BRCA', 'Duchenne muscular dystrophy', "
        "'hereditary cancer', 'genetic testing', 'lynch syndrome', or 'pharmacogenetic'. "
        "Exclude any documents that contain the phrase 'providal guideline', or that are press releases, claim forms, newsletters, blog posts, or provider manuals."
        "Only include links from official sources such as the insurance company’s website or regulatory bodies. with direct PDF links and ofiicial HTML policy pages."
        "If a document is available as a downloadable PDF, return the full direct PDF link under the key 'pdf_links'. "
        "If the document is only available as a webpage, return the full URL under the key 'webpage_links'. "
        "The JSON response must follow this exact format: "
        "{\"pdf_links\": [list of direct PDF links], \"webpage_links\": [list of webpage URLs]}. "
        "Make sure the lists contain only valid, existing URLs. If no documents are found, return empty lists. "
        "Do not include any explanation, markdown, natural language, or formatting — only return the raw JSON object."
    )

prompt_functions = {
    "baseline": policy_retrieval_prompt_baseline,
    "keyword_checked_document": policy_retrieval_prompt_keyword_checked_document,
    "keyword_verified_links": policy_retrieval_prompt_keyword_verified_links
}



def download_pdf(url, save_path):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Downloaded PDF: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download PDF from {url}: {e}")
        return False


def save_webpage_as_pdf(url, save_path):
    try:
        pdfkit.from_url(url, save_path)
        print(f"✅ Saved webpage as PDF: {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to save {url} as PDF: {e}")
        return False
    
def query_llm_for_providers(messages, model="ChatGPT", openai_client=None, perplexity_api_key=None, max_retries=3):
    def call_ChatGPT():
        prompt = messages[-1]["content"]  
        response = openai_client.responses.create(
            model="gpt-4o",
            input=messages,
            tools=[{"type": "web_search_preview"}]
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
            print(f"🔁 Attempt {attempt} ({model})...")
            return call_perplexity() if model == "Perplexity" else call_ChatGPT()
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
    return None


def extract_provider_json(response_text):
    original = response_text.strip()

    # Step 1: Try direct JSON
    try:
        result = json.loads(original)
        if isinstance(result, dict) and "pdf_links" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Step 2: Try cleanup of ```json blocks
    response_text = re.sub(r"^```json\s*|\s*```$", "", original, flags=re.IGNORECASE).strip()
    
    # Step 3: Try parsing again
    try:
        result = json.loads(response_text)
        if isinstance(result, dict) and "pdf_links" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Step 4: Find first JSON block in messy response
    json_match = re.search(r"(\{[\s\S]*?\})", original)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            if isinstance(result, dict) and "pdf_links" in result:
                return result
        except json.JSONDecodeError as e:
            print("⚠️ Still invalid JSON block:", e)

    print("⚠️ Could not parse JSON. Using fallback empty provider list.")
    return {
        "pdf_links": [],
        "webpage_links": []
    }


    
def retrieve_and_save_policy(provider, prompt_fn, model="ChatGPT", prompt_name="baseline", openai_client=None, perplexity_api_key=None, experiment_id = None):
    '''
    Retrieves genetic testing policy links for the given provider using the specified prompt.
    Returns a dictionary containing retrieval result summary.
    '''
    print(f"\n🔍 Searching for: {provider}")
    messages = [
        {"role": "system", "content": "You are a helpful and precise research assistant."},
        {"role": "user", "content": prompt_fn(provider)}
    ]

    try:
        response_text = query_llm_for_providers(
            messages, model=model, openai_client=gpt_client, perplexity_api_key=perplexity_api_key
        )
        print(f"\n🧾 {model.upper()} raw response for '{provider}':\n{response_text}\n")
        result_json = extract_provider_json(response_text)

        pdf_links = result_json.get("pdf_links", [])
        webpage_links = result_json.get("webpage_links", [])
        all_links = pdf_links + webpage_links

        folder = os.path.join(LLM_FOLDER_ROOT, model, f"{prompt_name}_experiment{experiment_id}", provider.replace(" ", "_"))
        os.makedirs(folder, exist_ok=True)

        downloaded_pdfs = sum(
            download_pdf(link, os.path.join(folder, os.path.basename(link.split("?")[0])))
            for link in pdf_links
        )

        saved_webpages = sum(
            save_webpage_as_pdf(
                link,
                os.path.join(folder, f"{os.path.basename(link.split('?')[0]).split('.')[0] or 'webpage'}.pdf")
            ) for link in webpage_links
        )

        return {
            "Provider": provider,
            "PDF Links": json.dumps(pdf_links),
            "PDF Count": len(pdf_links),
            "Downloaded PDFs": downloaded_pdfs,
            "Webpage Links": json.dumps(webpage_links),
            "Webpage Count": len(webpage_links),
            "Saved Webpages as PDF": saved_webpages,
            "All Links": json.dumps(all_links),
            "Total Count": len(all_links)
        }

    except Exception as e:
        print(f"❌ Error processing {provider}: {e}")
        return {
            "Provider": provider,
            "PDF Links": "[]",
            "PDF Count": 0,
            "Downloaded PDFs": 0,
            "Webpage Links": "[]",
            "Webpage Count": 0,
            "Saved Webpages as PDF": 0,
            "All Links": "[]",
            "Total Count": 0
        }

def summarize_policy_retrieval(providers, prompt_fn, model="ChatGPT", prompt_name="baseline", experiment_id=None,
                                openai_client=None, perplexity_api_key=None, base_output_dir="llm_results"):
    """
    Summarizes retrieval results from ChatGPT or Perplexity.
    """
    results = []
    for provider in providers:
        result = retrieve_and_save_policy(
            provider,
            prompt_fn,
            model=model,
            prompt_name=prompt_name,
            openai_client=gpt_client,
            perplexity_api_key=perplexity_api_key
        )
        results.append(result)

    df = pd.DataFrame(results)
    numeric_cols = ["PDF Count", "Downloaded PDFs", "Webpage Count", "Saved Webpages as PDF", "Total Count"]

    sum_row = df[numeric_cols].sum().to_dict()
    sum_row["Provider"] = "TOTAL_SUM"

    avg_row = df[numeric_cols].mean().round(2).to_dict()
    avg_row["Provider"] = "AVERAGE"

    df = pd.concat([df, pd.DataFrame([sum_row, avg_row])], ignore_index=True)
    print(f"📊 Summary DataFrame:\n{df}")

    model_folder = os.path.join(base_output_dir, model)
    os.makedirs(model_folder, exist_ok=True)
    output_path = os.path.join(model_folder, f"{prompt_name}_experiment{experiment_id}.csv")

    df.to_csv(output_path, index=False)
    print(f"📄 Combined results saved to: {output_path}")

    return df


def evaluate_md5_comparisons(results, model="ChatGPT", prompt_name="baseline",
                              manual_folder=MANUAL_FOLDER,
                              llm_root=LLM_FOLDER_ROOT,
                              output_dir=BASE_RESULT_DIR,
                              return_stats=False,
                              custom_output_path=None,
                              experiment_id=None):
    """
    Compares MD5 hashes of LLM-downloaded files with manually curated ones.

    Args:
        results: List of retrieval result dicts.
        model: "ChatGPT" or "perplexity" to locate correct LLM folder.
        prompt_name: Name of the prompt, used for folder disambiguation.
        manual_folder: Path to manually curated documents.
        llm_root: Root folder containing LLM-generated content.
        output_dir: Where to save the MD5 comparison results.
        return_stats: If True, return match counts.
        custom_output_path: Optional override for CSV save path.

    Returns:
        Updated results with MD5 stats added or summary dict (if return_stats=True).
    """
    matched_rows = []
    llm_only_rows = []
    md5_stats = {}

    def compute_md5(file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def get_md5_map(folder):
        md5_map = {}
        for root, _, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)
                md5_map[file] = compute_md5(path)
        return md5_map

    llm_root_model = os.path.join(llm_root, model, prompt_name)
    global_key = f"{model}_{prompt_name}"
    global_md5_set = set()

    for row in results:
        provider = row["Provider"]
        if provider in ["TOTAL_SUM", "AVERAGE"]:
            continue

        print(f"\n📂 Comparing files for '{provider}'...")
        llm_folder = os.path.join(llm_root_model, provider.replace(" ", "_"))

        manual_hashes = get_md5_map(manual_folder)
        llm_hashes = get_md5_map(llm_folder)

        manual_md5_set = set(manual_hashes.values())
        llm_md5_set = set(llm_hashes.values())
        global_md5_set |= llm_md5_set

        matched = manual_md5_set & llm_md5_set
        only_llm = llm_md5_set - manual_md5_set

        md5_stats[provider] = {
            "MD5 Matched": len(matched),
            "LLM Only": len(only_llm)
        }

        link_map = {}
        try:
            pdf_links = json.loads(row.get("PDF Links", "[]"))
            webpage_links = json.loads(row.get("Webpage Links", "[]"))
            for link in pdf_links + webpage_links:
                fname = os.path.basename(link.split("?")[0])
                link_map[fname] = link
        except Exception:
            print(f"⚠️ Could not parse links for {provider}")

        for filename, md5 in llm_hashes.items():
            link = link_map.get(filename, "")
            entry = {
                "Provider": provider,
                "Filename": filename,
                "MD5": md5,
                "Link": link
            }
            if md5 in matched:
                print(f"✔️ MATCHED: {filename}")
                entry["Status"] = "MATCHED"
                matched_rows.append(entry)
            elif md5 in only_llm:
                print(f"❌ UNMATCHED (LLM-only): {filename}")
                entry["Status"] = "LLM_ONLY"
                llm_only_rows.append(entry)

    for row in results:
        provider = row["Provider"]
        row["MD5 Matched"] = md5_stats.get(provider, {}).get("MD5 Matched", 0)
        row["LLM Only"] = md5_stats.get(provider, {}).get("LLM Only", 0)

    if matched_rows or llm_only_rows:
        md5_df = pd.DataFrame(matched_rows + llm_only_rows)
        output_path = (
            custom_output_path
            if custom_output_path
            else os.path.join(
                output_dir,
                "md5",
                model,
                prompt_name,
                f"{model}_md5_comparison_{prompt_name}"
                + (f"_experiment{experiment_id}" if experiment_id is not None else "")
                + ".csv"
            )
        )

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        md5_df.to_csv(output_path, index=False)
        print(f"📄 MD5 results saved to: {output_path}")

    if return_stats:
        total_match = sum(stat["MD5 Matched"] for stat in md5_stats.values())
        total_llm = sum(stat["LLM Only"] for stat in md5_stats.values())

        stats_df = pd.DataFrame([
            {"Provider": k, **v} for k, v in md5_stats.items()
        ])
        stats_path = os.path.join(
            output_dir,
            "md5",
            model,
            prompt_name,
            f"{model}_md5_stats_summary_{prompt_name}"
            + (f"_experiment{experiment_id}" if experiment_id is not None else "")
            + ".csv"
        )

        os.makedirs(os.path.dirname(stats_path), exist_ok=True)
        stats_df.to_csv(stats_path, index=False)
        print(f"📄 MD5 stats summary saved to: {stats_path}")

        return {
            "match_count": total_match,
            "llm_only_count": total_llm
        }

    return results

def compute_md5_set_for_model_prompt(model_path):
    import hashlib, os

    md5_set = set()

    def compute_md5(file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    for root, _, files in os.walk(model_path):
        for f in files:
            path = os.path.join(root, f)
            md5_set.add(compute_md5(path))
    return md5_set

def compare_md5_union_intersection(model_a, model_b, prompt_name, output_dir, experiment_id=None):
    """
    Computes and compares MD5 hash sets between two models for a given prompt.
    Saves union/intersection stats as a CSV file, with optional experiment ID tagging.

    Args:
        model_a (str): First model name (e.g., "ChatGPT")
        model_b (str): Second model name (e.g., "Perplexity")
        prompt_name (str): Prompt variant name (e.g., "keyword_filtered")
        output_dir (str): Base directory for saving results
        experiment_id (int or None): Optional experiment index to disambiguate multiple runs
    """
    path_a = os.path.join(LLM_FOLDER_ROOT, model_a, prompt_name)
    path_b = os.path.join(LLM_FOLDER_ROOT, model_b, prompt_name)

    set_a = compute_md5_set_for_model_prompt(path_a)
    set_b = compute_md5_set_for_model_prompt(path_b)

    union = set_a | set_b
    intersection = set_a & set_b

    print(f"\n🔬 MD5 UNION COUNT between {model_a} and {model_b} ({prompt_name}): {len(union)}")
    print(f"🔬 MD5 INTERSECTION COUNT: {len(intersection)}")

    # Create output folder
    save_folder = os.path.join(output_dir, "md5", prompt_name)
    os.makedirs(save_folder, exist_ok=True)

    # Construct filename with experiment_id
    filename = f"md5_union_intersection_{prompt_name}"
    if experiment_id is not None:
        filename += f"_experiment{experiment_id}"
    filename += ".csv"

    union_path = os.path.join(save_folder, filename)

    # Save results
    pd.DataFrame([{
        "Prompt": prompt_name,
        "Model A": model_a,
        "Model B": model_b,
        "Experiment ID": experiment_id,
        "MD5 Union Count": len(union),
        "MD5 Intersection Count": len(intersection)
    }]).to_csv(union_path, index=False)

    print(f"📄 Cross-model MD5 union/intersection saved to: {union_path}")


def run_policy_experiments_multiple_times(n_trials=3, providers=None):
    if providers is None:
        providers = ["United Healthcare"]
    base_output_dir = os.path.join(BASE_RESULT_DIR, "retrieval")

    for experiment_id in range(1, n_trials + 1):
        print(f"\n🚀 Running policy retrieval trial {experiment_id}...\n")

        for model in ["ChatGPT", "Perplexity"]:
            for prompt_name, prompt_fn in prompt_functions.items():
                print(f"→ Model: {model}, Prompt: {prompt_name}")

                for provider in providers:
                    retrieve_and_save_policy(
                        provider=provider,
                        model=model,
                        prompt_name=prompt_name,
                        prompt_fn=prompt_fn,
                        experiment_id=experiment_id
                    )

                df = summarize_policy_retrieval(
                    providers=providers,
                    prompt_fn=prompt_fn,
                    model=model,
                    prompt_name=prompt_name,
                    experiment_id=experiment_id,
                    openai_client=gpt_client,
                    perplexity_api_key=perplexity_api_key,
                    base_output_dir=base_output_dir
                )

                df_clean = df[~df["Provider"].isin(["TOTAL_SUM", "AVERAGE"])]
                md5_output_path = os.path.join(
                    BASE_RESULT_DIR,
                    "md5",
                    model,
                    prompt_name,
                    f"{model}_md5_comparison_{prompt_name}_experiment{experiment_id}.csv"
                )

                evaluate_md5_comparisons(
                    results=df_clean.to_dict(orient="records"),
                    model=model,
                    prompt_name=prompt_name,
                    manual_folder=MANUAL_FOLDER,
                    llm_root=LLM_FOLDER_ROOT,
                    output_dir=BASE_RESULT_DIR,
                    custom_output_path=md5_output_path,
                    experiment_id=experiment_id
                )

        for prompt_name in prompt_functions:
            compare_md5_union_intersection(
                model_a="ChatGPT",
                model_b="Perplexity",
                prompt_name=prompt_name,
                output_dir=BASE_RESULT_DIR,
                experiment_id=experiment_id
            )

if __name__ == "__main__":
    print("🔁 Starting full policy retrieval experiment loop...\n")
    run_policy_experiments_multiple_times(n_trials=2)
    print("\n✅ All experiments completed successfully.")
