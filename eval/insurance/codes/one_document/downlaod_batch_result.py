import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

#base_results_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n"
batches = []

#for root, dirs, files in os.walk(base_results_dir):
#    if "batch_id.txt" in files:
#        batch_id_path = os.path.join(root, "batch_id.txt")
#        with open(batch_id_path, "r") as f:
#            batch_id = f.read().strip()
        
#        save_dir = os.path.dirname(batch_id_path)
#        batches.append({
#            "batch_id": batch_id,
#            "save_dir": save_dir
#        })

test_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/one_doc/final/gpt-4o"
batch_logs_dir = os.path.join(test_dir, "batch_logs")

if os.path.exists(os.path.join(batch_logs_dir, "batch_id.txt")):
    with open(os.path.join(batch_logs_dir, "batch_id.txt"), "r") as f:
        batch_id = f.read().strip()
    
    batches.append({
        "batch_id": batch_id,
        "save_dir": test_dir  # test_run2가 save_dir
    })

print(f"total {len(batches)} batches checking...")

for i, batch_info in enumerate(batches):
    batch_id = batch_info["batch_id"]
    save_dir = batch_info["save_dir"]
    
    print(f"\n[{i+1}] batch {batch_id}")
    
    batch = client.batches.retrieve(batch_id)
    print(f"status: {batch.status}")
    
    if batch.status == "completed":
        
        # 결과 파일 다운로드
        content = client.files.content(batch.output_file_id)
        lines = content.text.strip().split('\n')
        
        qna_dir = os.path.join(save_dir, "qna_raw")
        os.makedirs(qna_dir, exist_ok=True)
        
        for line in lines:
            result = json.loads(line)
            case_id = result["custom_id"].split("|")[0]
            #print(f"Full result structure: {json.dumps(result, indent=2)}")
            #break

            response_text = result["response"]["body"]["output"][-1]["content"][0]["text"]

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

            print(f"Saved: {case_id}")
            file_path = os.path.join(qna_dir, f"{case_id}_qna.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"stored: {len(lines)} files")

    elif batch.status == "failed":
        print("❌ failed")
    else:
        print("⏳ processing...")

print("\nsuccess!")
