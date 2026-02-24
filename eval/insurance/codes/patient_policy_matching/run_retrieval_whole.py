import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from eval.insurance.codes.patient_policy_matching.load_policy import load_policies, calculate_pdf_md5
from embedding_policies import embed_policies_from_headers
from rerank_whole import rerank_whole_policies
from eval.insurance.codes.patient_policy_matching.calculate_match_rate import calculate_match_rate
from eval.insurance.codes.patient_policy_matching.md5_matching import md5_match_by_rerank_order
from eval.insurance.codes.patient_policy_matching.retrieve_candidates import retrieve_candidates

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)

def run_retrieval_evaluation_whole(dataset_path, base_dir, embedding_matrix, doc_names, policies, md5s, llm_models=None, openai_client=chatgpt_agent, perplexity_api_key=perplexity_api_key, top_k_values=None, k_retrieval=5, embedder_id="text-embedding-3-small"):
    
    if llm_models is None:
        llm_models = ['gpt-5-mini']
    if top_k_values is None:
        top_k_values = [1]
        
    # Load dataset
    with open(dataset_path, 'r') as f:
        case_ex = json.load(f)
    
    results = {}
    
    for llm_model in llm_models:
        for top_k in top_k_values:
            print(f"Processing {llm_model} with top_k={top_k}")
            
            rerank_failed_cases = []  
            api_failed_cases = []     
            success_count = 0  
            
            # Process each case
            for case in case_ex:
                cid = case["id"]
                patient_info_text = case["patient_info"]
                expected = case["expected_md5"]

                print(f"  Case {cid}...", end=" ")

                try:
                    # Retrieve candidates
                    cands = retrieve_candidates(
                        vecs=embedding_matrix,
                        names=doc_names,
                        query_text=patient_info_text,
                        doc_texts=policies,
                        embedder_id=embedder_id,
                        vecs_normalized=True,
                        k=k_retrieval
                    )

                    # Rerank with LLM
                    order, rerank_success = rerank_whole_policies(
                        patient_info=patient_info_text,
                        candidates=cands,
                        llm_model=llm_model,
                        openai_client=chatgpt_agent,           
                        perplexity_api_key=perplexity_api_key,
                        save_dir=base_dir,
                        case_id=cid,
                        top_k=top_k,
                        return_success=True 
                    )

                    if not rerank_success:
                        rerank_failed_cases.append({
                            "case_id": cid,
                            "reason": "Rerank failed"
                        })

                    # Check match
                    md5_match_by_rerank_order(
                        candidates=cands,
                        order=order,
                        md5s=md5s,                
                        expected_md5=expected,
                        save_dir=base_dir,   
                        case_id=cid,
                        retrieval_model=llm_model,
                        top_k=top_k,
                        embedding_matrix=embedding_matrix,
                        doc_names=doc_names, 
                        query_text=patient_info_text,
                        embedder_id=embedder_id
                    )

                    success_count += 1

                except Exception as e:
                    api_failed_cases.append({
                        "case_id": cid,
                        "error": str(e)[:200]
                    })

            # Calculate match rate
            model_name = llm_model.replace("-", "_")
            log_dir = f"{base_dir}/retrieval/{model_name}/top{top_k}"
            os.makedirs(log_dir, exist_ok=True)
            
            if rerank_failed_cases:
                with open(f"{log_dir}/rerank_failed_cases.json", 'w') as f:
                    json.dump(rerank_failed_cases, f, indent=2)
                print(f"  ⚠️ Rerank failed: {len(rerank_failed_cases)} cases")
            
            if api_failed_cases:
                with open(f"{log_dir}/api_failed_cases.json", 'w') as f:
                    json.dump(api_failed_cases, f, indent=2)
                print(f"  ✗ API failed: {len(api_failed_cases)} cases")
            
            csv_path = f"{base_dir}/retrieval/{model_name}/top{top_k}/matching_summary.csv"
            match_rate, matched, total = calculate_match_rate(csv_path)
            results[f"{llm_model}_top{top_k}"] = match_rate
            print(f"Match Rate: {match_rate:.2%} ({matched}/{total})")
    
    return results

if __name__ == "__main__":
    dataset_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/sample_qna_free_text.json"
    folder = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_answer_real"
    save_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/toy_openai"
    os.makedirs(save_dir, exist_ok=True)

    policies, md5s, headers = load_policies(folder)

    embeddings, doc_names, embedding_matrix = embed_policies_from_headers(
        headers=policies,
        md5s=md5s,
        cache_dir= save_dir,
        embedder_id="text-embedding-3-small",
        cache_suffix="whole_example_example"
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        all_cases = json.load(f)

    test_cases = all_cases[3:4]

    temp_dataset = os.path.join(save_dir, "test_cases.json")
    with open(temp_dataset, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)

    results = run_retrieval_evaluation_whole(
        dataset_path=temp_dataset,
        base_dir=save_dir,
        embedding_matrix=embedding_matrix,
        doc_names=doc_names,
        policies=policies,
        md5s=md5s,
        llm_models=['gpt-5-mini'],
        top_k_values= [1],
        k_retrieval=10,
        embedder_id="text-embedding-3-small"
    )
    print("Final Results:", results)