import os
import json
import pandas as pd
import re

def merge_json_to_csv(base_dir, qna_model, output_filename="qna_results.csv"):
    '''Merge multiple JSON files from PDF QnA experiment into a single CSV file'''

    folder_path = os.path.join(base_dir, "LLM_QnA", "one_doc", "final", qna_model, "qna_raw")
    output_csv_path = os.path.join(folder_path, output_filename)

    all_data = []

    json_files = [f for f in os.listdir(folder_path) if f.endswith("_qna.json")]
    json_files.sort()

    for filename in json_files:
        json_path = os.path.join(folder_path, filename)
        case_id = filename.replace("_qna.json", "")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            flat = {"case_id": case_id}
            qr = data.get("qna_result", {})
            if isinstance(qr, dict) and "raw" in qr:     
                s = str(qr["raw"])
                m = re.search(r"\{[\s\S]*\}", s)          
                try:
                    qr = json.loads(m.group(0)) if m else {}
                except Exception:
                    qr = {}

            for k in ["Q0","Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8"]:
                flat[k] = qr.get(k, "")

            token_usage = data.get("token_usage", {})
            for k, v in token_usage.items():
                flat[f"token_{k}"] = v
            all_data.append(flat)
        except Exception as e:
            print(f"Error processing {json_path}: {e}")

    if not all_data:
        return None
    df = pd.DataFrame(all_data)
    df.to_csv(output_csv_path, index=False)
    print(f"processed: {output_csv_path}")

    return df

def merge_all_models_to_csv(base_dir, qna_models, output_filename="merged_qna_results.csv"):
    '''merge results from multiple models into a single CSV file'''
    all_data = []
    
    for model in qna_models:
        model_csv_path = os.path.join(base_dir, "LLM_QnA", "one_doc", "final", model, "qna_raw", "qna_results.csv")

        if os.path.exists(model_csv_path):
            df = pd.read_csv(model_csv_path)
            df['model'] = model  
            all_data.append(df)
            print(f"✅ {model}: {len(df)}")
        else:
            print(f"⚠️ {model}: no results - {model_csv_path}")
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        output_path = os.path.join(base_dir, "LLM_QnA", "one_doc", "final", output_filename)
        final_df.to_csv(output_path, index=False)
        
        print(f"\n🎉 merged all!")
        print(f"location: {output_path}")
        
        return final_df
    else:
        print("❗ no data to merge.")
        return None