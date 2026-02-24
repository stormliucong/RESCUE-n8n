import os
from compare_md5 import compare_md5
from merge_results import merge_results

def main():
    result_base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/payer_retrieval/final"
    existing_pdfs_base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_ret"

    payers = ["United Healthcare", "Aetna", "Cigna", "Blue Cross and Blue Shield Federal Employee Program"]
    models = ["gpt-4o", "gpt-5-mini"]
    prompt_types = ["baseline", "keyword", "verified"]

    payer_mapping = {
        "United Healthcare": "United Healthcare",
        "Aetna": "Aetna",
        "Cigna": "Cigna",
        "Blue Cross and Blue Shield Federal Employee Program": "BCBS FEP"
    }

    for iteration in range(1, 4):
        for model in models:
            for prompt_type in prompt_types:
                for payer in payers:
                    exp_dir = os.path.join(result_base_dir, f"iteration_{iteration}", model, prompt_type, payer.replace(" ", "_"))
                    downloaded_csv = os.path.join(exp_dir, "downloaded_pdfs.csv")
                    output_csv = os.path.join(exp_dir, "md5_comparison_results.csv")
                    
                    if os.path.exists(downloaded_csv):
                        compare_md5(downloaded_csv, existing_pdfs_base_dir, output_csv, payer_mapping)

    merge_results(result_base_dir, os.path.join(result_base_dir, "all_assessments.csv"), os.path.join(result_base_dir, "all_links.csv"))

if __name__ == "__main__":
    main()