import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv("OPEN_AI_API_KEY"))

batch_id = "batch_68fa7260b9c4819082ecb3c363a28585"  
# batch_id = "batch_68fa752f557c81908ffd3832c7124898"

print(f"Checking batch: {batch_id}")

batch = client.batches.retrieve(batch_id)
print(f"Status: {batch.status}")

if batch.status == "completed" and batch.output_file_id:
    content = client.files.content(batch.output_file_id)
    lines = content.text.strip().split('\n')
    
    print(f"\nTotal lines: {len(lines)}")
    print("\nChecking first error case...\n")
    
    for line in lines:
        result = json.loads(line)
        case_id = result["custom_id"].split("|")[0]
        
        output_list = result["response"]["body"]["output"]
        print(f"Output array length: {len(output_list)}")

        print("\nOutput types:")
        for i, item in enumerate(output_list):
            print(f"  [{i}] type: {item.get('type')}")

        try:
            text1 = result["response"]["body"]["output"][1]["content"][0]["text"]
            print(f"output[1] text: {text1[:100]}...")
        except Exception as e:
            print(f"output[1] failed: {e}")

        try:
            text2 = result["response"]["body"]["output"][-1]["content"][0]["text"]
            print(f"output[-1] text: {text2[:100]}...")
        except Exception as e:
            print(f"output[-1] failed: {e}")