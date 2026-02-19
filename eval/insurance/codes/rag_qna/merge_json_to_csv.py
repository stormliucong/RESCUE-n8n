import os
import json
import pandas as pd


def process_json_files(json_folder_path, output_csv_path):
    '''read multiple JSON files in a folder and merge them into a single CSV file'''
    all_data = []
    json_files = [f for f in os.listdir(json_folder_path) if f.endswith("_qna.json")]
    json_files.sort()
    
    for filename in json_files:
        json_path = os.path.join(json_folder_path, filename)
        case_id = filename.replace("_qna.json", "")
        
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            flat = {"case_id": case_id}
            qna_result = data.get("qna_result", {})
            for k, v in qna_result.items():
                flat[k] = v

            token_usage = data.get("token_usage", {})
            flat["token_input"] = token_usage.get("input_tokens", 0)
            flat["token_output"] = token_usage.get("output_tokens", 0)
            flat["token_total"] = token_usage.get("total_tokens", 0)
            
            all_data.append(flat)
        except Exception as e:
            print(f"Error processing {json_path}: {e}")
    
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(output_csv_path, index=False)
        print(f"Saved: {output_csv_path}")
        return df
    else:
        return None

def process_combo_folder(folder_path):
    '''Process a combo folder containing RAG and baseline JSON files'''
    results = {}
    
    # RAG
    rag_path = os.path.join(folder_path, "qna_raw")
    if os.path.exists(rag_path):
        csv_path = os.path.join(rag_path, "qna_results_rag.csv")
        rag_df = process_json_files(rag_path, csv_path)
        print(rag_df)
        if rag_df is not None:
            results["rag"] = rag_df

    # Baseline
    baseline_path = os.path.join(folder_path, "qna_raw", "baseline")
    if os.path.exists(baseline_path):
        csv_path = os.path.join(baseline_path, "qna_results_baseline.csv")
        baseline_df = process_json_files(baseline_path, csv_path)
        print(baseline_df)
        if baseline_df is not None:
            results["baseline"] = baseline_df
    
    return results

def merge_json_to_csv(base_dir, results_subpath=None):
    '''Merge JSON files from multiple combo folders into CSV files'''
    all_results = {}
    if results_subpath is None:
        results_subpath = os.path.join("results", "LLM_QnA", "RAG", "final")
    results_path = os.path.join(base_dir, results_subpath)
    combo_folders = [f for f in os.listdir(results_path) if f.startswith("top")]
    
    for combo_folder in combo_folders:
        folder_path = os.path.join(results_path, combo_folder)
        print(f"Processing: {combo_folder}")
        results = process_combo_folder(folder_path)
        all_results[combo_folder] = results
    
    return all_results

def json_to_csv(json_folder, output_csv):
    """JSON 파일들을 CSV로 변환"""
    all_data = []
    json_files = [f for f in os.listdir(json_folder) if f.endswith("_qna.json")]
    
    for filename in sorted(json_files):
        json_path = os.path.join(json_folder, filename)
        case_id = filename.replace("_qna.json", "")
        
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            flat = {"case_id": case_id}
            qna_result = data.get("qna_result", {})
            flat.update(qna_result)
            
            token_usage = data.get("token_usage", {})
            flat["token_input"] = token_usage.get("input_tokens", 0)
            flat["token_output"] = token_usage.get("output_tokens", 0)
            flat["token_total"] = token_usage.get("total_tokens", 0)
            
            all_data.append(flat)
        except Exception as e:
            print(f"❌ {json_path}: {e}")
    
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(output_csv, index=False)
        print(f"✅ {output_csv}")
        return True
    return False

if __name__ == "__main__":
    import tempfile

    base_dir = tempfile.mkdtemp(prefix="qna_merge_")
    retrieval_model = "gpt-5-mini"
    qna_model = "gpt-4o-mini"
    top_k = 3

    folder = os.path.join(
        base_dir, "qna_raw",
        f"{retrieval_model}_{qna_model}".replace("-", "_"),
        f"top{top_k}"
    )
    rag_folder = os.path.join(folder, "qna_raw")
    os.makedirs(rag_folder, exist_ok=True)

    baseline_folder = os.path.join(rag_folder, "baseline")
    os.makedirs(baseline_folder, exist_ok=True)

    with open(os.path.join(rag_folder, "CaseA_qna.json"), "w", encoding="utf-8") as f:
        json.dump({
            "qna_result": {
                "Q0": "WGS",
                "Q1": "No",
                "Q2": "Not Specified",
                "Q3": "No"
            },
            "token_usage": {
                "input": 120,
                "output": 80,
                "total": 200
            }
        }, f)

    with open(os.path.join(rag_folder, "CaseB_qna.json"), "w", encoding="utf-8") as f:
        json.dump({
            "qna_result": {
                "Q0": "BRCA1/2",
                "Q1": "Yes",
                "Q2": "Not Specified",
                "Q3": "Yes"
            },
            "token_usage": {
                "input": 130,
                "output": 90,
                "total": 220
            }
        }, f)

    with open(os.path.join(baseline_folder, "CaseC_qna.json"), "w", encoding="utf-8") as f:
        json.dump({
            "qna_result": {
                "Q0": "WES",
                "Q1": "No",
                "Q2": "Not Specified",
                "Q3": "No"
            },
            "token_usage": {
                "input": 140,
                "output": 100,
                "total": 240
            }
        }, f)

    with open(os.path.join(baseline_folder, "CaseD_qna.json"), "w", encoding="utf-8") as f:
        json.dump({
            "qna_result": {
                "Q0": "CMA",
                "Q1": "Yes",
                "Q2": "Not Specified",
                "Q3": "Yes"
            },
            "token_usage": {
                "input": 150,
                "output": 110,
                "total": 260
            }
        }, f)

    results = merge_json_to_csv(base_dir, results_subpath="qna_raw/gpt_5_mini_gpt_4o_mini")
    print(results)

    combo_data = list(results.values())[0]
    df1 = combo_data["rag"]
    df2 = combo_data["baseline"]

    assert set(df1["case_id"]) == {"CaseA", "CaseB"}
    assert set(df2["case_id"]) == {"CaseC", "CaseD"}
