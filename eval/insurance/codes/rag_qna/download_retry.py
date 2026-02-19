import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"
retry_batches = []

# batch_id_retry.txt 찾기
for root, dirs, files in os.walk(base_dir):
    if "batch_id_retry.txt" in files:
        with open(os.path.join(root, "batch_id_retry.txt")) as f:
            batch_id = f.read().strip()
        
        save_dir = os.path.dirname(os.path.dirname(root))
        case_type = os.path.basename(root)
        retry_batches.append((batch_id, save_dir, case_type))

print(f"Found {len(retry_batches)} retry batches\n")

for batch_id, save_dir, case_type in retry_batches:
    print(f"Downloading: {os.path.basename(save_dir)}/{case_type}")
    
    batch = client.batches.retrieve(batch_id)
    print(f"  Status: {batch.status}")
    
    if batch.status == "completed" and batch.output_file_id:
        content = client.files.content(batch.output_file_id)
        lines = content.text.strip().split('\n')
        
        qna_dir = os.path.join(save_dir, "qna_raw", case_type)
        
        for line in lines:
            result = json.loads(line)
            case_id = result["custom_id"].split("|")[0]
            
            response_text = result["response"]["body"]["output"][-1]["content"][0]["text"]
            qna_result = json.loads(response_text)
            
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
            with open(file_path, "w") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ Downloaded {len(lines)} files")

print("\n✅ Done!")