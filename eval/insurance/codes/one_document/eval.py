import os
import json
import pandas as pd

def evaluate_qna_results(base_dir, qna_model, ground_truth_json_path):
    '''Evaluate QnA results against ground truth and save evaluation metrics to CSV'''
    Questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    
    qna_csv_path = os.path.join(base_dir, "LLM_QnA", "one_doc", "final", qna_model, "qna_raw", "qna_results.csv")
    
    df = pd.read_csv(qna_csv_path)
    with open(ground_truth_json_path, "r") as f:
        gt_data = json.load(f)
    
    results = []
    for _, row in df.iterrows():
        case_id = row["case_id"]
        gt_entry = gt_data.get(case_id)
        
        if not gt_entry:
            continue
        
        correct = 0
        total = 9  
        
        for q in Questions:
            pred = str(row.get(q, "")).strip()
            true = str(gt_entry.get(q, "")).strip()
            if pred == true and pred != "":
                correct += 1
        
        accuracy = 100 * correct / total
        results.append({
            "case_id": case_id,
            "correct": correct,
            "total": total,
            "accuracy": accuracy
        })
    
    eval_df = pd.DataFrame(results)
    eval_dir = os.path.join(base_dir, "LLM_QnA", "one_doc", "final", "eval")
    os.makedirs(eval_dir, exist_ok=True)
    output_path = os.path.join(eval_dir, f"{qna_model}_evaluation.csv")
    eval_df.to_csv(output_path, index=False)
    
    overall_acc = eval_df["accuracy"].mean()
    total_correct = eval_df["correct"].sum()
    total_questions = eval_df["total"].sum()
    ti = pd.to_numeric(df.get("token_input_tokens", pd.Series(dtype=float)), errors="coerce").mean()
    to = pd.to_numeric(df.get("token_output_tokens", pd.Series(dtype=float)), errors="coerce").mean()
    tt = pd.to_numeric(df.get("token_total_tokens", pd.Series(dtype=float)), errors="coerce").mean()
    
    print(f"🎯 {qna_model} result:")
    print(f"   Overall accuracy: {overall_acc:.1f}%")
    print(f"   Correct answers: {total_correct}/{total_questions}")
    print(f"   Evaluated cases: {len(eval_df)}")
    print(f"   Output path: {output_path}")
    print(f"   Avg. Tokens - Input: {ti:.1f}, Output: {to:.1f}, Total: {tt:.1f}\n")

    return eval_df

def analyze_question_accuracy_from_merged(merged_csv_path, ground_truth_json_path):
    '''accuracy analysis for each question from merged qna_results.csv'''
    
    # Read data
    df = pd.read_csv(merged_csv_path)
    with open(ground_truth_json_path, "r") as f:
        gt_data = json.load(f)
    
    questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    
    overall_results = []
    for q in questions:
        correct = 0
        total = 0
        accuracies = []
        
        for _, row in df.iterrows():
            case_id = row["case_id"]
            if case_id in gt_data:
                pred = str(row[q]).strip()
                true = str(gt_data[case_id][q]).strip()
                
                if pred == true and pred != "":
                    correct += 1
                    accuracies.append(1)
                else:
                    accuracies.append(0)
                total += 1
        
        accuracy = round(correct / total * 100, 2) if total > 0 else 0
        p = correct / total if total else 0
        std_accuracy = round((p * (1 - p) / total) ** 0.5 * 100, 2) if total else 0
        overall_results.append({"question": q, "accuracy": accuracy, "std": std_accuracy, "correct": correct, "total": total})
        print(f"{q}: {accuracy}% ± {std_accuracy}% (SE) ({correct}/{total})")
    
    rag_dir = os.path.dirname(os.path.dirname(merged_csv_path))
    output_dir = os.path.join(rag_dir, "eval")
    os.makedirs(output_dir, exist_ok=True)

    overall_df = pd.DataFrame(overall_results)
    overall_df.to_csv(os.path.join(output_dir, "overall_question_accuracy.csv"), index=False)
    print(f"\n result saved: {output_dir}")
    return overall_df