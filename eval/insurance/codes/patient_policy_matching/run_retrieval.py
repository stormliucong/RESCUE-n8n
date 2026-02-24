import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from eval.insurance.codes.patient_policy_matching.load_policy import load_policies, calculate_pdf_md5
from embedding_policies import embed_policies_from_headers
from rerank_policies import rerank_policies
from eval.insurance.codes.patient_policy_matching.calculate_match_rate import calculate_match_rate
from eval.insurance.codes.patient_policy_matching.md5_matching import md5_match_by_rerank_order
from eval.insurance.codes.patient_policy_matching.retrieve_candidates import retrieve_candidates

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)

def run_retrieval_evaluation(dataset_path, base_dir, embedding_matrix, doc_names, headers, md5s, llm_models=None, openai_client=chatgpt_agent, perplexity_api_key=perplexity_api_key, top_k_values=None, k_retrieval=5, embedder_id="all-MiniLM-L6-v2"):
    
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
            
            # Process each case
            for case in case_ex:
                cid = case["id"]
                patient_info_text = case["patient_info"]
                expected = case["expected_md5"]

                # Retrieve candidates
                cands = retrieve_candidates(
                    vecs=embedding_matrix,
                    names=doc_names,
                    query_text=patient_info_text,
                    doc_texts=headers,
                    embedder_id=embedder_id,
                    vecs_normalized=True,
                    k=k_retrieval
                )

                # Rerank with LLM
                order = rerank_policies(
                    patient_info=patient_info_text,
                    candidates=cands,
                    llm_model=llm_model,
                    openai_client=chatgpt_agent,           
                    perplexity_api_key=perplexity_api_key,
                    save_dir=base_dir,
                    case_id=cid,
                    top_k=top_k 
                )

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

            # Calculate match rate
            model_name = llm_model.replace("-", "_")
            csv_path = f"{base_dir}/retrieval/{model_name}/top{top_k}/matching_summary.csv"
            match_rate, matched, total = calculate_match_rate(csv_path)
            results[f"{llm_model}_top{top_k}"] = match_rate
            print(f"Match Rate: {match_rate:.2%} ({matched}/{total})")
    
    return results

if __name__ == "__main__":
    folder = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_answer_real"
    policies, md5s, headers = load_policies(folder)

    embeddings, doc_names, embedding_matrix = embed_policies_from_headers(
        headers=headers,
        md5s=md5s,
        cache_dir="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset",
        embedder_id="all-MiniLM-L6-v2",
        cache_suffix="update"
    )
    results = run_retrieval_evaluation(
        dataset_path="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/sample_qna_free_text.json",
        base_dir="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset",
        embedding_matrix=embedding_matrix,
        doc_names=doc_names,
        headers=headers,
        md5s=md5s,
        llm_models=['perplexity'],
        top_k_values= [5],
        k_retrieval=10,
        embedder_id="all-MiniLM-L6-v2"
    )
    print("Final Results:", results)