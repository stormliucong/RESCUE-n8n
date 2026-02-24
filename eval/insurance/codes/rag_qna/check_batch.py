import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

# problem_batches = [
#     ("batch_68fa6da81d348190ac07d2d4c750572d", "top1_30retrieve_gpt_5_gpt_5_mini_update"),
#     ("batch_68fa7293ff388190b52a5a60acb09d57", "top3_10retrieve_gpt_5_gpt_5_mini_update"),
#     ("batch_68fa7260b9c4819082ecb3c363a28585", "top3_10retrieve_gpt_5_mini_gpt_5_mini_update")
# ]

# for batch_id, folder in problem_batches:
#     print(f"\n{'='*60}")
#     print(f"Folder: {folder}")
#     print(f"Batch: {batch_id}")
    
#     batch = client.batches.retrieve(batch_id)
#     print(f"Status: {batch.status}")
#     print(f"Request counts: {batch.request_counts}")
    
#     if batch.output_file_id:
#         print(f"Output file: {batch.output_file_id}")
#     else:
#         print("⚠️ No output file!")
    
#     if batch.error_file_id:
#         print(f"❌ Error file: {batch.error_file_id}")

#     batch_id = "batch_68fa6da81d348190ac07d2d4c750572d"
#     batch = client.batches.retrieve(batch_id)

#     if batch.output_file_id:
#         content = client.files.content(batch.output_file_id)
#         lines = content.text.strip().split('\n')
    
#         print(f"Total lines in batch output: {len(lines)}")
#         print(f"Expected: 67")
#         print(f"Downloaded (unmatched): 20")
#         print(f"Downloaded (baseline): 67")
    
#     # 첫 번째 결과 확인
#         first_result = json.loads(lines[0])
#         print(f"\nFirst result custom_id: {first_result['custom_id']}")
#         print(f"Response status: {first_result['response']['status_code']}")
    
#     # 모든 custom_id 확인
#         custom_ids = [json.loads(line)['custom_id'] for line in lines]
#         print(f"\nSample custom_ids:")
#         for cid in custom_ids[:5]:
#             print(f"  {cid}")

#     batches = [
#         ("unmatched", "batch_68fa6d967da08190918963315c387d84"),
#         ("baseline", "batch_68fa752584048190a4b8c3317c073d31")
#     ]

#     for case_type, batch_id in batches:
#         batch = client.batches.retrieve(batch_id)
#         print(f"\n{case_type}:")
#         print(f"  Status: {batch.status}")
#         print(f"  Counts: {batch.request_counts}")

#     batch_id = "batch_68fa7293ff388190b52a5a60acb09d57"
#     batch = client.batches.retrieve(batch_id)

#     if batch.error_file_id:
#         error_content = client.files.content(batch.error_file_id)
#         error_lines = error_content.text.strip().split('\n')
#     print(f"Failed cases: {len(error_lines)}")
    
#     for i, line in enumerate(error_lines[:3]):  # 처음 3개만
#         error = json.loads(line)
#         print(f"\n[{i+1}] {error['custom_id']}")
#         print(f"  Error code: {error['response']['status_code']}")
#         print(f"  Error: {error['response']['body']['error']['message'][:100]}...")

base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"

# # batch_id_retry.txt 찾기
# for root, dirs, files in os.walk(base_dir):
#     if "batch_id_retry.txt" in files:
#         with open(os.path.join(root, "batch_id_retry.txt")) as f:
#             batch_id = f.read().strip()
        
#             folder = os.path.basename(os.path.dirname(os.path.dirname(root)))
#             case_type = os.path.basename(root)
        
#             batch = client.batches.retrieve(batch_id)
#             print(f"\n{folder}/{case_type}")
#             print(f"  Batch: {batch_id}")
#             print(f"  Status: {batch.status}")
#             print(f"  Progress: {batch.request_counts}")

combos = [
    "top3_10retrieve_gpt_5_gpt_5_update",
    "top3_10retrieve_gpt_5_mini_gpt_5_update"
]

for combo in combos:
    batch_id_path = os.path.join(base_dir, combo, "qna_raw/unmatched_baseline/batch_id.txt")
    
    with open(batch_id_path) as f:
        batch_id = f.read().strip()
    
    batch = client.batches.retrieve(batch_id)
    
    print(f"\n{'='*60}")
    print(f"{combo}/unmatched_baseline")
    print(f"Batch: {batch_id}")
    print(f"Status: {batch.status}")
    print(f"Counts: {batch.request_counts}")
    
    if batch.error_file_id:
        print(f"❌ Error file exists!")