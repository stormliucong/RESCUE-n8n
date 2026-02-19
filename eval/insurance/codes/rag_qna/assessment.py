import os
from eval_qna import evaluate_qna_results, compare_topk_averages_from_merged, compare_topk_for_all_models_from_merged, analyze_question_accuracy_from_merged
from calculate_match_rate import calculate_match_rate, combine_match_rate
from merge_json_to_csv import merge_json_to_csv, process_json_files, process_combo_folder
from merge_results import merge_all_qna_results

def main():
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance"
    answer_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/ground_truth.json"

    print("Step 1: Converting JSON to CSV for each folder...")
    merge_json_to_csv(BASE_DIR)
    
    print("Step 1.5: Combining match rates...")
    results_path = os.path.join(BASE_DIR, "results", "LLM_QnA", "RAG", "final")
    
    pairs = [
        # top1, 10retrieve
    ("top1_10retrieve_gpt_5_gpt_5_update",               "gpt_5",      "gpt_5",      10, 1),
    ("top1_10retrieve_gpt_5_gpt_5_mini_update",          "gpt_5",      "gpt_5_mini", 10, 1),
    ("top1_10retrieve_gpt_5_mini_gpt_5_update",          "gpt_5_mini", "gpt_5",      10, 1),
    ("top1_10retrieve_gpt_5_mini_gpt_5_mini_update",     "gpt_5_mini", "gpt_5_mini", 10, 1),

    # top1, 30retrieve
    ("top1_30retrieve_gpt_5_gpt_5_update",               "gpt_5",      "gpt_5",      30, 1),
    ("top1_30retrieve_gpt_5_gpt_5_mini_update",          "gpt_5",      "gpt_5_mini", 30, 1),
    ("top1_30retrieve_gpt_5_mini_gpt_5_update",          "gpt_5_mini", "gpt_5",      30, 1),
    ("top1_30retrieve_gpt_5_mini_gpt_5_mini_update",     "gpt_5_mini", "gpt_5_mini", 30, 1),

    # top3, 10retrieve
    ("top3_10retrieve_gpt_5_gpt_5_update",               "gpt_5",      "gpt_5",      10, 3),
    ("top3_10retrieve_gpt_5_gpt_5_mini_update",          "gpt_5",      "gpt_5_mini", 10, 3),
    ("top3_10retrieve_gpt_5_mini_gpt_5_update",          "gpt_5_mini", "gpt_5",      10, 3),
    ("top3_10retrieve_gpt_5_mini_gpt_5_mini_update",     "gpt_5_mini", "gpt_5_mini", 10, 3),

    # top3, 30retrieve
    ("top3_30retrieve_gpt_5_gpt_5_update",               "gpt_5",      "gpt_5",      30, 3),
    ("top3_30retrieve_gpt_5_gpt_5_mini_update",          "gpt_5",      "gpt_5_mini", 30, 3),
    ("top3_30retrieve_gpt_5_mini_gpt_5_update",          "gpt_5_mini", "gpt_5",      30, 3),
    ("top3_30retrieve_gpt_5_mini_gpt_5_mini_update",     "gpt_5_mini", "gpt_5_mini", 30, 3),
    ]
    model_configs = []
    for combo, rmodel, qmodel, rcount, topk in pairs:
        model_configs.append({
            "combo_folder": combo,
            "top_k": topk,
            "retrieval_count": rcount,
            "retrieval_model": rmodel,
            "qna_model": qmodel
        })

    # output_csv = os.path.join(results_path, "all_match_rates.csv")
    # combine_match_rate(pairs_with_path, output_csv)

    print("Step 2: qna performance")
    for config in model_configs:
        combo = config["combo_folder"]
        rag_csv = os.path.join(results_path, combo, "qna_raw", "qna_results_rag.csv")
        baseline_csv = os.path.join(results_path, combo, "qna_raw", "baseline", "qna_results_baseline.csv")
    
        if os.path.exists(rag_csv):
            rag_out = os.path.join(results_path, combo, "qna_raw", "qna_eval_rag.csv")
            evaluate_qna_results(BASE_DIR, rag_csv, answer_path, rag_out)
    
        if os.path.exists(baseline_csv):
            baseline_out = os.path.join(results_path, combo, "qna_raw", "baseline", "qna_eval_baseline.csv")
            evaluate_qna_results(BASE_DIR, baseline_csv, answer_path, baseline_out)


    print("Step 3: Merging all qna results...")
    merge_all_qna_results(
        parent_dir=BASE_DIR,
        model_configs=model_configs
    )

    print("Step 4: Analyzing merged results...")
    rag_merged_csv = os.path.join(results_path, "all_rag_results_merged.csv")
    baseline_merged_csv = os.path.join(results_path, "all_baseline_results_merged.csv")

    if os.path.exists(rag_merged_csv):
        analyze_question_accuracy_from_merged(rag_merged_csv, answer_path)
    else:
        print(f"Not found: {rag_merged_csv}")

    if os.path.exists(baseline_merged_csv):
        analyze_question_accuracy_from_merged(baseline_merged_csv, answer_path)
    else:
        print(f"Not found: {baseline_merged_csv}")

if __name__ == "__main__":
    main()