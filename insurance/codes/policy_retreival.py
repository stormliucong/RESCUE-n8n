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
client = OpenAI(api_key=openai_api_key)

ROOT_DIR = "/home/cptaswadu/RESCUE-n8n/insurance"
BASE_RESULT_DIR = os.path.join(ROOT_DIR, "results/policy_retrieval")
BASE_LLM_FOLDER = os.path.join(BASE_RESULT_DIR, "llm_searched")
manual_folder = os.path.join(ROOT_DIR, "insurance_policy")

def get_next_iteration_folder(prompt_name, trial, root=BASE_LLM_FOLDER):
    folder_name = f"{prompt_name}_trial{trial}"
    full_path = os.path.join(root, folder_name)
    os.makedirs(full_path, exist_ok=True)
    return full_path

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

def policy_retrieval_prompt_keyword(provider_name):
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

def policy_retrieval_prompt_strict(provider_name):
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
    "keyword": policy_retrieval_prompt_keyword,
    "strict": policy_retrieval_prompt_strict
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
    
def retrieve_and_save_policy(provider, prompt_fn, iteration_folder):
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
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=messages
        )

        result_text = response.output_text.strip().replace("```json", "").replace("```", "").strip()
        result_json = json.loads(result_text)

        pdf_links = result_json.get("pdf_links", [])
        webpage_links = result_json.get("webpage_links", [])
        all_links = pdf_links + webpage_links

        folder = os.path.join(iteration_folder, provider.replace(" ", "_"))
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
    
def summarize_policy_retrieval(providers, prompt_fn, output_csv_path=None, iteration_folder=None):
    '''
    Collects and summarizes policy retrieval results for a list of insurance providers using a specified prompt function.
    Saves a combined CSV with retrieval statistics per provider, as well as total and average rows.

    Args:
        providers (list of str): List of insurance provider names.
        prompt_fn (function): Prompt function to generate the search prompt (e.g., policy_retrieval_prompt_keyword).

    Returns:
        DataFrame containing per-provider retrieval results and summary rows.
    '''
    results = []

    for provider in providers:
        result = retrieve_and_save_policy(provider, prompt_fn, iteration_folder)
        results.append(result)

    # Add total and average rows
    df = pd.DataFrame(results)
    numeric_cols = ["PDF Count", "Downloaded PDFs", "Webpage Count", "Saved Webpages as PDF", "Total Count"]

    sum_row = df[numeric_cols].sum().to_dict()
    sum_row["Provider"] = "TOTAL_SUM"

    avg_row = df[numeric_cols].mean().round(2).to_dict()
    avg_row["Provider"] = "AVERAGE"

    df = pd.concat([df, pd.DataFrame([sum_row, avg_row])], ignore_index=True)

    # Save to CSV
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    print(f"📄 Combined results saved to: {output_csv_path}")

    return df

def evaluate_md5_comparisons(results, manual_folder, llm_root,
                              output_dir, return_stats=False, custom_output_path=None):
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

    for row in results:
        provider = row["Provider"]
        if provider in ["TOTAL_SUM", "AVERAGE"]:
            continue

        print(f"\n📂 Comparing files for '{provider}'...")
        llm_folder = os.path.join(llm_root, provider.replace(" ", "_"))

        manual_hashes = get_md5_map(manual_folder)
        llm_hashes = get_md5_map(llm_folder)

        manual_md5_set = set(manual_hashes.values())
        llm_md5_set = set(llm_hashes.values())

        matched = manual_md5_set & llm_md5_set
        only_llm = llm_md5_set - manual_md5_set

        md5_stats[provider] = {
            "MD5 Matched": len(matched),
            "LLM Only": len(only_llm)
        }

        # Build link map
        link_map = {}
        try:
            pdf_links = json.loads(row.get("PDF Links", "[]"))
            webpage_links = json.loads(row.get("Webpage Links", "[]"))
            for link in pdf_links + webpage_links:
                fname = os.path.basename(link.split("?")[0])
                link_map[fname] = link
        except Exception:
            print(f"⚠️ Could not parse links for {provider}")

        # Match/unmatch tracking
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
        os.makedirs(output_dir, exist_ok=True)
        output_path = custom_output_path if custom_output_path else os.path.join(output_dir, "md5_comparison.csv")
        md5_df.to_csv(output_path, index=False)
        print(f"📄 MD5 results saved to: {output_path}")

    if return_stats:
        total_match = sum(stat["MD5 Matched"] for stat in md5_stats.values())
        total_llm = sum(stat["LLM Only"] for stat in md5_stats.values())
        return {
            "match_count": total_match,
            "llm_only_count": total_llm
        }

    return results


def run_retrieval_trials(providers, prompt_fns, num_trials=3, base_output_path="insurance/results/policy_retrieval/"):
    md5_trial_stats = []
    combined_stats_summary = []

    retrieval_dir = os.path.join(base_output_path, "retrieval")
    md5_dir = os.path.join(base_output_path, "md5")
    os.makedirs(retrieval_dir, exist_ok=True)
    os.makedirs(md5_dir, exist_ok=True)

    for prompt_name, prompt_fn in prompt_fns.items():
        all_prompt_trials = []

        for trial in range(1, num_trials + 1):
            iteration_folder = get_next_iteration_folder(prompt_name, trial)

            trial_output_path = os.path.join(retrieval_dir, f"{prompt_name}_trial{trial}.csv")
            df = summarize_policy_retrieval(providers, prompt_fn, output_csv_path=trial_output_path, iteration_folder=iteration_folder)
            df["Prompt"] = prompt_name
            df["Trial"] = trial
            all_prompt_trials.append(df)

            print(f"\n✅ [{prompt_name} | Trial {trial}] Retrieval saved to:")
            print(f"   📄 {trial_output_path}")

            df_cleaned = df[~df["Provider"].isin(["TOTAL_SUM", "AVERAGE"])]
            md5_output_path = os.path.join(md5_dir, f"{prompt_name}_trial{trial}_md5.csv")

            eval_result = evaluate_md5_comparisons(
                df_cleaned.to_dict(orient="records"),
                manual_folder="/home/cptaswadu/RESCUE-n8n/insurance/insurance_policy",
                llm_root=iteration_folder,
                output_dir=base_output_path,
                custom_output_path=md5_output_path,
                return_stats=True
            )

            md5_trial_stats.append({
                "Prompt": prompt_name,
                "Trial": trial,
                "Match_Count": eval_result["match_count"],
                "LLM_Only_Count": eval_result["llm_only_count"]
            })

        df_combined = pd.concat(all_prompt_trials, ignore_index=True)
        df_cleaned_combined = df_combined[~df_combined["Provider"].isin(["TOTAL_SUM", "AVERAGE"])]
        numeric_cols = ["PDF Count", "Downloaded PDFs", "Webpage Count", "Saved Webpages as PDF", "Total Count"]

        mean_vals = df_cleaned_combined[numeric_cols].mean().round(2).to_dict()
        std_vals = df_cleaned_combined[numeric_cols].std().round(2).to_dict()

        combined_stat = {"Prompt": prompt_name}
        for col in numeric_cols:
            combined_stat[f"{col}_Mean"] = mean_vals[col]
            combined_stat[f"{col}_Std"] = std_vals[col]
        combined_stats_summary.append(combined_stat)

    pd.DataFrame(combined_stats_summary).to_csv(os.path.join(base_output_path, "prompt_combined_stats.csv"), index=False)
    pd.DataFrame(md5_trial_stats).to_csv(os.path.join(base_output_path, "md5_stats_by_trial.csv"), index=False)

    print("\n🎉 Retrieval + MD5 evaluation summary complete.")



def main():
    providers = ["United Healthcare", "Aetna"]
    prompt_fns = prompt_functions
    run_retrieval_trials(providers, prompt_fns, num_trials=3)

if __name__ == "__main__":
    main()

