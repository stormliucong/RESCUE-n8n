import os
import re
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)

def rerank_policies(patient_info, candidates, llm_model,
                    openai_client=None, max_preview_chars=1000,
                    save_dir=None, case_id=None, top_k=None, return_success=False):
    '''Re-rank a list of candidate insurance policies using an LLM'''
    if not candidates:
        raise ValueError("No candidates provided to rerank_policies().")

    top_k = int(top_k) if top_k is not None else None

    # Preview candidate texts (truncate and clean newlines)
    candidate_texts = [f"{c[0]}\n{str(c[2] or '')[:max_preview_chars].replace('\n',' ')}" for c in candidates]

    # Build LLM prompt
    prompt = f"""You are an expert insurance policy analyst specializing in genetic testing coverage.

You will be given patient information and K candidate insurance policies.
Re-rank ALL candidates from best (1) to worst (K), considering coverage fit for the patient's clinical context, insurer and genetic test.
Return ONLY a JSON array of integers that is a strict permutation of [1 to K]. No extra text.

Patient Information:
{patient_info}

Candidate Policies (numbered):
""" + "\n\n".join([f"Policy {i+1}:\n{t}" for i, t in enumerate(candidate_texts)]) 

    messages = [
        {"role": "system", "content": "You are an information extraction system for ranking the most appropriate insurance policies."},
        {"role": "user", "content": prompt}
    ]

    success = False
    # Call GPT models
    try:
        if llm_model.lower().startswith("gpt"):
            if openai_client is None:
                raise ValueError("openai_client is required for GPT models.")
            api_params = {
                "model": llm_model,
                "messages": messages
            }
        # Only set temperature for non-GPT-5 models
            if "gpt-5" not in llm_model.lower():
                api_params["temperature"] = 0
            response = openai_client.chat.completions.create(**api_params)
            result = response.choices[0].message.content.strip()

        else:
            raise ValueError(f"Unsupported LLM model: {llm_model}")
        
        # Parse the numeric choice from the LLM output
        print(f"Case {case_id}: LLM Response: {result[:500]}")
        m = re.search(r"\[(.*?)\]", result, flags=re.S)
        arr = json.loads("[" + m.group(1) + "]") if m else None
        # validate & convert to 0-based
        k = len(candidates)
        if arr and isinstance(arr, list) and len(arr) == k and set(arr) == set(range(1, k+1)):
            order = [min(max(int(x)-1, 0), k-1) for x in arr]
            success = True  
            if case_id:
                print(f"Case {case_id}: Rerank SUCCESS")
        else:
            order = list(range(k))
            success = False
            if case_id:
                print(f"Case {case_id}: Rerank FAILED (invalid output)")
    
    except Exception as e:
        k = len(candidates)
        order = list(range(k))
        success = False
        if case_id:
            print(f"Case {case_id}: LLM reranking failed ({e}). Using original order.")

    if save_dir and case_id:
        safe_model = (llm_model or "unknown").replace("-", "_")

        final_dir = os.path.join(save_dir, "retrieval", safe_model)
        if top_k is not None: 
            final_dir = os.path.join(final_dir, f"top{top_k}")
        os.makedirs(final_dir, exist_ok=True)

        csv_path = os.path.join(final_dir, "rerank_orders.csv")
        file_exists = os.path.exists(csv_path)

        with open(csv_path, "a", encoding="utf-8") as f:
            if not file_exists:
                f.write("case_id,rank,name,score,rerank_success\n")
        
            for rpos, idx in enumerate(order, start=1):
                name, score, _ = candidates[idx]
                f.write(f"{case_id},{rpos},{name},{score},{success}\n")
    
    if return_success:
        return order, success
    else:
        return order