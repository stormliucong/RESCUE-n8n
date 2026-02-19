import os
import json
import pandas as pd

def evaluate_qna_results(base_dir, combination_folder_name, ground_truth_json_path, out_csv_path=None):
    '''Evaluate QnA results against ground truth'''
    Questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]

    if combination_folder_name.endswith(".csv") and os.path.isfile(combination_folder_name):
        qna_csv_path = combination_folder_name
    else:
        qna_csv_path = os.path.join(base_dir, "results", "LLM_QnA", "RAG", "final", combination_folder_name, "qna_results.csv")
    
    df = pd.read_csv(qna_csv_path)
    with open(ground_truth_json_path, "r") as f:
        gt_data = json.load(f)

    rows = []
    for _, row in df.iterrows():
        case_id = row["case_id"]
        gt_entry = gt_data.get(case_id)
        if not gt_entry:
            continue

        correct = 0
        total = 0
        for q in Questions:
            pred = str(row.get(q, "")).strip()
            true = str(gt_entry.get(q, "")).strip()
            if pred == true and pred != "":
                correct += 1
            total += 1

        acc = 100 * correct / total if total > 0 else 0
        rows.append({
            "case_id": case_id,
            "correct": correct,
            "total": total,
            "accuracy": acc
        })

    eval_df = pd.DataFrame(rows)
    if out_csv_path is None:
        out_dir = os.path.join(base_dir, "results", "LLM_QnA", "RAG", "final", combination_folder_name, "eval")
        os.makedirs(out_dir, exist_ok=True)
        out_csv_path = os.path.join(out_dir, "qna_eval.csv")
        print(f"Evaluation results will be saved to: {out_csv_path}")
        
    eval_df.to_csv(out_csv_path, index=False)

    overall_acc = eval_df["accuracy"].mean()
    std_acc = eval_df["accuracy"].std()
    total_correct = eval_df["correct"].sum()
    total_questions = eval_df["total"].sum()
    mean_token_input = df["token_input"].mean() if "token_input" in df.columns else 0
    mean_token_output = df["token_output"].mean() if "token_output" in df.columns else 0

    summary_path = out_csv_path.replace(".csv", "_summary.csv")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("name,total_correct,total_questions,overall_acc,std_acc,mean_token_input,mean_token_output\n")
        f.write(f"Overall,{total_correct},{total_questions},{overall_acc:.2f},{std_acc:.2f},{mean_token_input:.2f},{mean_token_output:.2f}\n")
        
        print(f"Summary saved to: {summary_path}")
    print(f"Overall accuracy: {overall_acc:.2f}% ± {std_acc:.2f}%")
    print(f"Evaluated cases: {len(eval_df)}")

    return eval_df

def compare_topk_for_all_models_from_merged(merged_csv_path, ground_truth_json_path):
    '''Compare different top-k values for multiple model combinations from merged CSV'''
    
    df = pd.read_csv(merged_csv_path)
    with open(ground_truth_json_path, "r") as f:
        gt_data = json.load(f)
    
    questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    results = []
    
    for (combo_folder, top_k), group in df.groupby(['combo_folder', 'top_k']):
        total_correct = 0
        total_questions = 0
        accuracies = [] 
        
        for _, row in group.iterrows():
            case_id = row["case_id"]
            if case_id in gt_data:
                for q in questions:
                    pred = str(row[q]).strip()
                    true = str(gt_data[case_id][q]).strip()
                    if pred == true and pred != "":
                        total_correct += 1
                        accuracies.append(1)  
                    else:
                        accuracies.append(0)  
                    total_questions += 1
        
        if total_questions > 0:
            accuracy = round(total_correct / total_questions * 100, 2)
            std_accuracy = round(pd.Series(accuracies).std() * 100, 2) if len(accuracies) > 0 else 0
            mean_token_input = group["token_input"].mean() if "token_input" in group.columns else 0
            mean_token_output = group["token_output"].mean() if "token_output" in group.columns else 0

            results.append({
                "combo_folder": combo_folder,
                "top_k": top_k,
                "accuracy": accuracy,
                "std": std_accuracy,
                "correct": total_correct,
                "total": total_questions,
                "mean_token_input": round(mean_token_input, 1),
                "mean_token_output": round(mean_token_output, 1)
            })
    
    rag_dir = os.path.dirname(os.path.dirname(merged_csv_path))
    output_dir = os.path.join(rag_dir, "eval")
    os.makedirs(output_dir, exist_ok=True)
    df_results = pd.DataFrame(results)
    result_type = "rag" if "rag" in os.path.basename(merged_csv_path) else "baseline"
    df_results.to_csv(os.path.join(output_dir, f"models_topk_results_{result_type}.csv"), index=False)
    print(f"Results saved: {output_dir}/models_topk_results_{result_type}.csv") 
    
    return df_results

def compare_topk_averages_from_merged(merged_csv_path, ground_truth_json_path):
    '''Compare average performance for each top-k value from merged CSV'''
    
    df = pd.read_csv(merged_csv_path)
    with open(ground_truth_json_path, "r") as f:
        gt_data = json.load(f)
    
    questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    results = []

    for top_k, group in df.groupby('top_k'):
        model_accuracies = []
        topk_correct = 0
        topk_total = 0
        models_processed = 0

        for combo_folder, model_group in group.groupby('combo_folder'):
            model_correct = 0
            model_total = 0
            
            for _, row in model_group.iterrows():
                case_id = row["case_id"]
                if case_id in gt_data:
                    for q in questions:
                        pred = str(row[q]).strip()
                        true = str(gt_data[case_id][q]).strip()
                        if pred == true and pred != "":
                            model_correct += 1
                        model_total += 1
            
            topk_correct += model_correct
            topk_total += model_total
            models_processed += 1

            if model_total > 0:
                model_acc = model_correct / model_total * 100
                model_accuracies.append(model_acc)
        
        if topk_total > 0:
            avg_accuracy = round((topk_correct / topk_total) * 100, 2)
            std_accuracy = round(pd.Series(model_accuracies).std(), 2) if len(model_accuracies) > 1 else 0
            topk_token_input = group["token_input"].mean() if "token_input" in group.columns else 0
            topk_token_output = group["token_output"].mean() if "token_output" in group.columns else 0

            results.append({
                "top_k": top_k,
                "avg_accuracy": avg_accuracy,
                "std_accuracy": std_accuracy,
                "total_correct": topk_correct,
                "total_questions": topk_total,
                "models_count": models_processed,
                "avg_token_input": round(topk_token_input, 2),
                "avg_token_output": round(topk_token_output, 2)
            })
    
    rag_dir = os.path.dirname(os.path.dirname(merged_csv_path))
    output_dir = os.path.join(rag_dir, "eval")
    os.makedirs(output_dir, exist_ok=True)

    result_type = "rag" if "rag" in os.path.basename(merged_csv_path) else "baseline"
    df_results = pd.DataFrame(results)
    df_results.to_csv(os.path.join(output_dir, f"topk_average_comparison_{result_type}.csv"), index=False)
    print(f"Results saved: {output_dir}/topk_average_comparison_{result_type}.csv")

    return df_results

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
        std_accuracy = round(pd.Series(accuracies).std() * 100, 2) if len(accuracies) > 0 else 0
        overall_results.append({"question": q, "accuracy": accuracy, "std": std_accuracy, "correct": correct, "total": total})
        print(f"{q}: {accuracy}% ± {std_accuracy}% ({correct}/{total})")
    
    rag_dir = os.path.dirname(os.path.dirname(merged_csv_path))
    output_dir = os.path.join(rag_dir, "eval")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.basename(merged_csv_path).replace("_results_merged.csv", "")
    output_filename = f"{base_name}_question_accuracy.csv"
    overall_df = pd.DataFrame(overall_results)
    overall_df.to_csv(os.path.join(output_dir, output_filename), index=False)
    print(f"\n result saved: {output_dir}")
    return overall_df

if __name__ == "__main__":
    import tempfile, math
    base_dir = tempfile.mkdtemp(prefix="qna_eval_")
    retrieval_model = "gpt-5-mini"
    qna_model = "gpt-4o-mini"
    top_k = 1

    folder = os.path.join(
    base_dir, "qna_raw",
    f"{retrieval_model}_{qna_model}".replace("-", "_"),
    f"top{top_k}"
    )
    os.makedirs(folder, exist_ok=True)

    pred_A = {
        "Q0": "WES",
        "Q1": "Yes",
        "Q2": "Yes",
        "Q3": "Yes",
        "Q4": "Yes",
        "Q5": "Yes",
        "Q6": "Yes",
        "Q7": "81415",
        "Q8": "Yes"
    }

    pred_B = {
        "Q0": "WES",
        "Q1": "Yes",
        "Q2": "Yes",
        "Q3": "Yes",
        "Q4": "Yes",
        "Q5": "Yes",
        "Q6": "Yes",
        "Q7": "81415",
        "Q8": "Yes"
    }

    qna_csv_path = os.path.join(folder, "qna_results.csv")
    pd.DataFrame(
        [{"case_id":"CaseA", **pred_A},
        {"case_id":"CaseB", **pred_B}]
    ).to_csv(qna_csv_path, index=False)

    gt = {
        "CaseA": {
            "Q0": "WES",
            "Q1": "Yes",
            "Q2": "Yes",
            "Q3": "Yes",
            "Q4": "Yes",
            "Q5": "Yes",
            "Q6": "Yes",
            "Q7": "81415",
            "Q8": "Yes"
        },
        "CaseB": {
            "Q0": "WGS",
            "Q1": "No",
            "Q2": "No",
            "Q3": "No",
            "Q4": "No",
            "Q5": "No",
            "Q6": "No",
            "Q7": "82415",
            "Q8": "No"
        }
    }

    gt_path = os.path.join(base_dir, "ground_truth.json")
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(gt, f, ensure_ascii=False)

    eval_df = evaluate_qna_results(
        base_dir=base_dir,
        retrieval_model=retrieval_model,
        qna_model=qna_model,
        top_k=top_k,
        ground_truth_json_path=gt_path,
    )

    print(eval_df)

    assert set(eval_df["case_id"]) == {"CaseA", "CaseB"}

    rowA = eval_df[eval_df["case_id"] == "CaseA"].iloc[0]
    rowB = eval_df[eval_df["case_id"] == "CaseB"].iloc[0]
    assert int(rowA["correct"]) == 9 and int(rowA["total"]) == 9
    assert int(rowB["correct"]) == 0 and int(rowB["total"]) == 9
    assert math.isclose(float(rowA["accuracy"]), 100.0)
    assert math.isclose(float(rowB["accuracy"]), 0.0)

    model_combinations = [
        ("gpt-5", "gpt-5-nano"),  
        ("gpt-4o", "gpt-4o-mini"),
    ]
    topk_list = [1, 3]
    rows = [{"case_id": "CaseA", **pred_A}, {"case_id": "CaseB", **pred_B}]

    for retrieval_model, qna_model in model_combinations:
        combo = f"{retrieval_model}_{qna_model}".replace("-", "_")
        for top_k in topk_list:
            folder = os.path.join(base_dir, "qna_raw", combo, f"top{top_k}")
            os.makedirs(folder, exist_ok=True)
            csv_path = os.path.join(folder, "qna_results.csv")
            pd.DataFrame(rows).to_csv(csv_path, index=False)

    df_all = compare_topk_for_all_models(
        base_dir=base_dir,
        model_combinations=model_combinations,
        topk_list=topk_list,
        ground_truth_json_path=gt_path,
    )
    print("\n[all models × topk]\n", df_all)
    assert len(df_all) == 4
    assert set(df_all["top_k"]) == {1, 3}

    df_avg = compare_topk_averages(
        base_dir=base_dir,
        model_combinations=model_combinations,
        topk_list=topk_list,
        ground_truth_json_path=gt_path,
    )
    print("\n[topk averages]\n", df_avg)
    assert len(df_avg) == 2
    assert set(df_avg["top_k"]) == {1, 3}
    assert set(df_avg["avg_accuracy"]) == {50.0}
    assert set(df_avg["models_count"]) == {2}
    assert set(df_avg["total_correct"]) == {18}
    assert set(df_avg["total_questions"]) == {36}