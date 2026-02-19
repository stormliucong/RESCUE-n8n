import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

failed_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/failed_batches.json"
with open(failed_path) as f:
    failed_batches = json.load(f)

for fb in failed_batches:
    jsonl_path = os.path.join(fb["folder"], "qna_raw", fb["case_type"], "batch_qna_requests.jsonl")
    
    upload = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch = client.batches.create(input_file_id=upload.id, endpoint="/v1/responses", completion_window="24h")
    
    with open(os.path.join(fb["folder"], "qna_raw", fb["case_type"], "batch_id.txt"), "w") as f:
        f.write(batch.id)
    
    print(f"{fb['case_type']}: {batch.id}")

print("Done!")