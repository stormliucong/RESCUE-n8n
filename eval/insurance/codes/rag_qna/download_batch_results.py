import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

base_results_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results/open_ai/gpt_5_mini_gpt_5_mini"
batches = []

for root, dirs, files in os.walk(base_results_dir):
    if "batch_id.txt" in files:
        batch_id_path = os.path.join(root, "batch_id.txt")
        with open(batch_id_path, "r") as f:
            batch_id = f.read().strip()
        
        if "iter3" in root:
            if "baseline" in root and os.path.basename(root) == "iter3":
                save_dir = root
                case_type = ""
            else:
                save_dir = os.path.dirname(root)
                case_type = os.path.basename(root)

        else:
            save_dir = os.path.dirname(root)
            case_type = os.path.basename(root)
        
            if case_type not in ["all_correct", "all_incorrect"]:
                continue
        
            if "header_k30_rerank3" not in save_dir:
                continue
        
        batches.append({
            "batch_id": batch_id,
            "save_dir": save_dir,
            "case_type": case_type
        })

print(f"total {len(batches)} batches checking...")

failed_batches = []

for i, batch_info in enumerate(batches):
    batch_id = batch_info["batch_id"]
    save_dir = batch_info["save_dir"]
    case_type = batch_info["case_type"]

    print(f"\n[{i+1}] batch {batch_id}")
    
    qna_check_dir = os.path.join(save_dir, "qna_raw", case_type) if case_type else os.path.join(save_dir, "qna_raw")
    qna_files = []
    if os.path.exists(qna_check_dir):
        qna_files = [f for f in os.listdir(qna_check_dir) if f.endswith('_qna.json')]
    
    if qna_files:
        print("✅ already downloaded - skip")
        continue

    batch = client.batches.retrieve(batch_id)
    print(f"status: {batch.status}")
    
    if batch.status == "completed":
        if not batch.output_file_id:
            print("❌ no output file - save for retry")
            failed_batches.append({
                "batch_id": batch_id,
                "folder": save_dir,
                "case_type": case_type
            })
            continue

        content = client.files.content(batch.output_file_id)
        lines = content.text.strip().split('\n')
        
        for line in lines:
            result = json.loads(line)
            custom_id_parts = result["custom_id"].split("|")
            case_id = custom_id_parts[0]
            actual_case_type = custom_id_parts[2]

            qna_dir = os.path.join(save_dir, "qna_raw", actual_case_type) if actual_case_type else os.path.join(save_dir, "qna_raw")
            os.makedirs(qna_dir, exist_ok=True)

            try:
                response_text = result["response"]["body"]["output"][-1]["content"][0]["text"]
            except (KeyError, IndexError):
                print(f"❌ {case_id} response structure error - skip")
                continue

            if not response_text:
                print(f"❗ {case_id} empty content — skip")
                continue
            
            try:
                qna_result = json.loads(response_text)
            except Exception:
                qna_result = {"raw": response_text}

            usage = result["response"]["body"].get("usage", {})
            save_data = {
                "qna_result": qna_result,
                "token_usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                }
            }

            file_path = os.path.join(qna_dir, f"{case_id}_qna.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"✅ stored: {len(lines)} files in {case_type}")

    elif batch.status == "failed":
        print("❌ batch failed")
        failed_batches.append({  
            "batch_id": batch_id,
            "folder": save_dir,
            "case_type": case_type
        })
    else:
        print("⏳ processing...")

print("\n" + "="*50)
if failed_batches:
    failed_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/failed_batches.json"
    with open(failed_path, "w") as f:
        json.dump(failed_batches, f, indent=2)
    print(f"❌ {len(failed_batches)} failed batches saved to:")
    print(f"   {failed_path}")
else:
    print("✅ All batches downloaded successfully!")