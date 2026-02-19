import json
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

# 실패한 배치들
# failed_batches = [
#     ("batch_68fa7293ff388190b52a5a60acb09d57", "top3_10retrieve_gpt_5_gpt_5_mini_update", "unmatched"),
#     ("batch_68fa7260b9c4819082ecb3c363a28585", "top3_10retrieve_gpt_5_mini_gpt_5_mini_update", "unmatched"),
#     ("batch_68fa752584048190a4b8c3317c073d31", "top1_10retrieve_gpt_5_mini_gpt_5_mini_update", "unmatched_baseline")
# ]


base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"

# for batch_id, folder, case_type in failed_batches:
#     print(f"\n{'='*60}")
#     print(f"Processing: {folder}/{case_type}")
    
#     # 에러 파일에서 실패한 케이스 추출
#     batch = client.batches.retrieve(batch_id)
#     if not batch.error_file_id:
#         print("  No errors - skip")
#         continue
    
#     error_content = client.files.content(batch.error_file_id)
#     failed_custom_ids = [json.loads(line)['custom_id'] for line in error_content.text.strip().split('\n')]
    
#     print(f"  Failed: {len(failed_custom_ids)} cases")
    
#     # 원본 jsonl에서 실패한 케이스만 필터링
#     orig_jsonl = os.path.join(base_dir, folder, "qna_raw", case_type, "batch_qna_requests.jsonl")
#     retry_jsonl = os.path.join(base_dir, folder, "qna_raw", case_type, "batch_qna_requests_retry.jsonl")
    
#     with open(orig_jsonl, 'r') as f_in, open(retry_jsonl, 'w') as f_out:
#         for line in f_in:
#             req = json.loads(line)
#             if req['custom_id'] in failed_custom_ids:
#                 f_out.write(line)
    
#     # 업로드 & 배치 생성
#     upload = client.files.create(file=open(retry_jsonl, "rb"), purpose="batch")
#     new_batch = client.batches.create(input_file_id=upload.id, endpoint="/v1/responses", completion_window="24h")
    
#     # batch_id 저장
#     with open(os.path.join(base_dir, folder, "qna_raw", case_type, "batch_id_retry.txt"), "w") as f:
#         f.write(new_batch.id)
    
#     print(f"  ✅ New batch: {new_batch.id}")

# print("\n✅ Done!")

failed_baseline_batches = [
    ("batch_68fa75332dec8190b14ac5698fd35374", "top3_10retrieve_gpt_5_gpt_5_update"),
    ("batch_68fa752a39048190be2661723bab666f", "top3_10retrieve_gpt_5_mini_gpt_5_update")
]

for batch_id, folder in failed_baseline_batches:
    print(f"\n{'='*60}")
    print(f"Processing: {folder}/unmatched_baseline")
    
    # 에러 파일에서 실패한 케이스 추출
    batch = client.batches.retrieve(batch_id)
    error_content = client.files.content(batch.error_file_id)
    failed_custom_ids = [json.loads(line)['custom_id'] for line in error_content.text.strip().split('\n')]
    
    print(f"  Failed: {len(failed_custom_ids)} cases - {[cid.split('|')[0] for cid in failed_custom_ids]}")
    
    # 원본 jsonl에서 실패한 케이스만 필터링
    orig_jsonl = os.path.join(base_dir, folder, "qna_raw/unmatched_baseline/batch_qna_requests.jsonl")
    retry_jsonl = os.path.join(base_dir, folder, "qna_raw/unmatched_baseline/batch_qna_requests_retry.jsonl")
    
    with open(orig_jsonl, 'r') as f_in, open(retry_jsonl, 'w') as f_out:
        for line in f_in:
            req = json.loads(line)
            if req['custom_id'] in failed_custom_ids:
                f_out.write(line)
    
    # 업로드 & 배치 생성
    upload = client.files.create(file=open(retry_jsonl, "rb"), purpose="batch")
    new_batch = client.batches.create(input_file_id=upload.id, endpoint="/v1/responses", completion_window="24h")
    
    # batch_id 저장
    with open(os.path.join(base_dir, folder, "qna_raw/unmatched_baseline/batch_id_retry.txt"), "w") as f:
        f.write(new_batch.id)
    
    print(f"  ✅ New batch: {new_batch.id}")

print("\n✅ Done!")