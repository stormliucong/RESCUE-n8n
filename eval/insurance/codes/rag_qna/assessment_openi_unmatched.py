import os
import pandas as pd
from eval_qna import evaluate_qna_results, compare_topk_averages_from_merged, compare_topk_for_all_models_from_merged, analyze_question_accuracy_from_merged
from calculate_match_rate import calculate_match_rate, combine_match_rate
from merge_json_to_csv import merge_json_to_csv, process_json_files, process_combo_folder, json_to_csv
from merge_results import merge_all_qna_results

def merge_by_case_type(configs, output_path):
    """case_type별로 결과 merge"""
    all_dfs = []
    
    for config in configs:
        csv_path = config["csv_path"]
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df["combo_folder"] = config["combo_folder"]
            df["retrieval_model"] = config["retrieval_model"]
            df["qna_model"] = config["qna_model"]
            df["retrieval_count"] = config["retrieval_count"]
            df["top_k"] = config["top_k"]
            all_dfs.append(df)
    
    if all_dfs:
        merged = pd.concat(all_dfs, ignore_index=True)
        merged.to_csv(output_path, index=False)
        print(f"  ✅ Saved: {output_path} ({len(merged)} rows)")
        return True
    return False

def main():
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance"
    answer_path = os.path.join(BASE_DIR, "dataset/ground_truth.json")
    results_path = os.path.join(BASE_DIR, "results/LLM_QnA/RAG/final")
    
    # 실험 설정
    openai_configs = [
        ("top1_10retrieve_gpt_5_mini_header_openai_small", "gpt_5_mini", "gpt_5_mini", 10, 1, "header"),
        ("top3_10retrieve_gpt_5_mini_header_openai_small", "gpt_5_mini", "gpt_5_mini", 10, 3, "header"),
        ("top1_30retrieve_gpt_5_mini_header_openai_small", "gpt_5_mini", "gpt_5_mini", 30, 1, "header"),
        ("top3_30retrieve_gpt_5_mini_header_openai_small", "gpt_5_mini", "gpt_5_mini", 30, 3, "header"),
        ("top1_10retrieve_gpt_5_mini_policy_openai_small", "gpt_5_mini", "gpt_5_mini", 10, 1, "policy"),
        ("top3_10retrieve_gpt_5_mini_policy_openai_small", "gpt_5_mini", "gpt_5_mini", 10, 3, "policy"),
    ]
    
    sentence_configs = []
    for topk in [1, 3]:
        for retrieve in [10, 30]:
            for rmodel in ["gpt_5", "gpt_5_mini"]:
                for qmodel in ["gpt_5", "gpt_5_mini"]:
                    folder = f"top{topk}_{retrieve}retrieve_{rmodel}_{qmodel}_update"
                    sentence_configs.append((folder, rmodel, qmodel, retrieve, topk))
    
    all_configs = []
    
    print("=== Step 1: JSON to CSV ===\n")
    
    # OpenAI 처리
    for folder, rmodel, qmodel, retrieve, topk, exp_type in openai_configs:
        print(f"\n{folder}")
        exp_path = os.path.join(results_path, folder, "qna_raw")
        
        for case_type in ["matched", "unmatched"]:
            case_dir = os.path.join(exp_path, case_type)
            if not os.path.exists(case_dir):
                continue
            
            csv_path = os.path.join(case_dir, "qna_results.csv")
            if json_to_csv(case_dir, csv_path):
                eval_csv = os.path.join(case_dir, "qna_eval.csv")
                try:
                    evaluate_qna_results(BASE_DIR, csv_path, answer_path, eval_csv)
                    all_configs.append({
                        "combo_folder": folder,
                        "retrieval_model": rmodel,
                        "qna_model": qmodel,
                        "retrieval_count": retrieve,
                        "top_k": topk,
                        "case_type": case_type,
                        "csv_path": csv_path,
                        "eval_path": eval_csv
                    })
                except Exception as e:
                    print(f"  ❌ Eval: {e}")
    
    # Sentence Transformer 처리
    for folder, rmodel, qmodel, retrieve, topk in sentence_configs:
        print(f"\n{folder}")
        exp_path = os.path.join(results_path, folder, "qna_raw")
        
        for case_type in ["unmatched", "unmatched_baseline"]:
            case_dir = os.path.join(exp_path, case_type)
            if not os.path.exists(case_dir):
                continue
            
            csv_path = os.path.join(case_dir, "qna_results.csv")
            if json_to_csv(case_dir, csv_path):
                eval_csv = os.path.join(case_dir, "qna_eval.csv")
                try:
                    evaluate_qna_results(BASE_DIR, csv_path, answer_path, eval_csv)
                    all_configs.append({
                        "combo_folder": folder,
                        "retrieval_model": rmodel,
                        "qna_model": qmodel,
                        "retrieval_count": retrieve,
                        "top_k": topk,
                        "case_type": case_type,
                        "csv_path": csv_path,
                        "eval_path": eval_csv
                    })
                except Exception as e:
                    print(f"  ❌ Eval: {e}")
    
    print("\n\n=== Step 2: Merge All Results ===\n")
    # OpenAI
    matched_configs = [c for c in all_configs if c["case_type"] == "matched"]
    openai_unmatched_configs = [c for c in all_configs if c["case_type"] == "unmatched" and "openai" in c["combo_folder"]]

    # Sentence Transformer
    sentence_unmatched_configs = [c for c in all_configs if c["case_type"] == "unmatched" and "openai" not in c["combo_folder"]]
    baseline_configs = [c for c in all_configs if c["case_type"] == "unmatched_baseline"]

    # Matched merge (OpenAI만)
    if matched_configs:
        print(f"Merging {len(matched_configs)} matched configs...")
        matched_merged_path = os.path.join(results_path, "all_matched_results_merged.csv")
        merge_by_case_type(matched_configs, matched_merged_path)

    # OpenAI Unmatched merge
    if openai_unmatched_configs:
        print(f"Merging {len(openai_unmatched_configs)} OpenAI unmatched configs...")
        openai_unmatched_merged_path = os.path.join(results_path, "all_openai_unmatched_results_merged.csv")
        merge_by_case_type(openai_unmatched_configs, openai_unmatched_merged_path)

    # Sentence Transformer Unmatched merge
    if sentence_unmatched_configs:
        print(f"Merging {len(sentence_unmatched_configs)} Sentence unmatched configs...")
        sentence_unmatched_merged_path = os.path.join(results_path, "all_sentence_unmatched_results_merged.csv")
        merge_by_case_type(sentence_unmatched_configs, sentence_unmatched_merged_path)

    # Baseline merge
    if baseline_configs:
        print(f"Merging {len(baseline_configs)} baseline configs...")
        baseline_merged_path = os.path.join(results_path, "all_baseline_results_merged.csv")
        merge_by_case_type(baseline_configs, baseline_merged_path)

    print("\n\n=== Step 3: Analyze Merged Results ===\n")
    
    matched_merged = os.path.join(results_path, "all_matched_results_merged.csv")
    if os.path.exists(matched_merged):
        print("\n--- Matched Results ---")
        analyze_question_accuracy_from_merged(matched_merged, answer_path)

    # OpenAI Unmatched 분석
    openai_unmatched_merged = os.path.join(results_path, "all_openai_unmatched_results_merged.csv")
    if os.path.exists(openai_unmatched_merged):
        print("\n--- OpenAI Unmatched Results ---")
        analyze_question_accuracy_from_merged(openai_unmatched_merged, answer_path)

    # Sentence Unmatched 분석
    sentence_unmatched_merged = os.path.join(results_path, "all_sentence_unmatched_results_merged.csv")
    if os.path.exists(sentence_unmatched_merged):
        print("\n--- Sentence Unmatched Results ---")
        analyze_question_accuracy_from_merged(sentence_unmatched_merged, answer_path)

    # Baseline 분석
    baseline_merged = os.path.join(results_path, "all_baseline_results_merged.csv")
    if os.path.exists(baseline_merged):
        print("\n--- Baseline Results ---")
        analyze_question_accuracy_from_merged(baseline_merged, answer_path)
    print("\n\n✅ All Done!")


if __name__ == "__main__":
    main()