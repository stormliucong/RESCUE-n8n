import os, json

USE_BATCH_QNA = True
BATCH_JSONL_PATH = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/batch_qna_requests.jsonl"

def get_batch_jsonl_path(save_base_dir, case_type="matched"):
    p = os.path.join(save_base_dir,  case_type, "batch_qna_requests.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p

def enqueue_qna_batch_line(custom_id, model, input_text, jsonl_path=BATCH_JSONL_PATH):
    """Append one QnA request line for OpenAI Batch API (Responses endpoint)."""
    body = {
        "model": model,
        "input": input_text,
        "prompt_cache_key": "qna-template-v1",
        "text": {"format": {"type": "json_object"}}
    }
    line = {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/responses",
        "body": body
    }
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

def submit_qna_batch(openai_client, jsonl_path, log_dir):
    """Upload JSONL and create a batch job for /v1/responses."""
    upload = openai_client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch = openai_client.batches.create(
        input_file_id=upload.id,
        endpoint="/v1/responses",
        completion_window="24h"
    )
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, "batch_id.txt"), "w") as f:
        f.write(batch.id)
    print("QnA Batch ID:", batch.id)
    return batch.id

if __name__ == "__main__":
    import tempfile
    test_file = tempfile.mktemp(suffix=".jsonl")
    
    enqueue_qna_batch_line("test_001", "gpt-4o-mini", "test input", test_file)
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    print(f"Content: {content[:100]}...")