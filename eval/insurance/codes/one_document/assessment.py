import os
from merge_json_to_csv import merge_json_to_csv, merge_all_models_to_csv
from eval import evaluate_qna_results, analyze_question_accuracy_from_merged
import pandas as pd

def main():
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results"
    answer_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/ground_truth.json"
    qna_models = ["gpt-5-mini", "gpt-5"]

    print("Step 1: Converting JSON to CSV for each folder...")
    for model in qna_models:
        merge_json_to_csv(BASE_DIR, model)

    print("\nStep 2: Merging all model CSVs into one...")
    merge_all_models_to_csv(BASE_DIR, qna_models)

    print("\nStep 3: Evaluating each model's QnA results...")
    for model in qna_models:
        evaluate_qna_results(BASE_DIR, model, answer_path)

    print("\nStep 4: Analyzing question-wise accuracy from merged results...")
    merged_csv_path = os.path.join(BASE_DIR, "LLM_QnA", "one_doc", "final", "merged_qna_results.csv")
    analyze_question_accuracy_from_merged(merged_csv_path, answer_path)

if __name__ == "__main__":
    main()