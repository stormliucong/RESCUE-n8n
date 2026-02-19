import os
import json
import pandas as pd
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI
from load_policy import load_policies, calculate_pdf_md5
from embedding_policies import embed_policies_from_headers
from retrieve_candidates import retrieve_candidates, cosine_topk
from rerank_policies import rerank_policies
from md5_matching import md5_match_by_rerank_order
from run_retrieval import run_retrieval_evaluation
from run_retrieval_whole import run_retrieval_evaluation_whole


def main():
    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)
    
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset"
    DATASET_PATH = f"{BASE_DIR}/qna_free_text_sample.json"
    POLICY_FOLDER = f"{BASE_DIR}/insurance_policy"

    K_RETRIEVAL_HEADER = [10, 30]
    K_RETRIEVAL_POLICY = [10]
    K_RERANK_LIST = [1, 3]
    RETRIEVAL_MODELS = ["gpt-5-mini"]
    EMBEDDER = "text-embedding-3-small"
    RESULTS_BASE = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"

    print("Loading policies...")
    policies, md5s, headers = load_policies(POLICY_FOLDER)

    print("Creating embeddings...") 
    embeddings_header, doc_names_header, embedding_matrix_header = embed_policies_from_headers(headers=headers, md5s=md5s, cache_dir=BASE_DIR, embedder_id=EMBEDDER, cache_suffix="headers_openai" )
    embeddings_policy, doc_names_policy, embedding_matrix_policy = embed_policies_from_headers(headers=policies, md5s=md5s, cache_dir=BASE_DIR, embedder_id=EMBEDDER, cache_suffix="policy_openai" )

    all_results = {}
    
    for K_RETRIEVAL in K_RETRIEVAL_HEADER:
        for K_RERANK in K_RERANK_LIST:

            SAVE_BASE_DIR = (
                f"{RESULTS_BASE}/"
                f"top{K_RERANK}_{K_RETRIEVAL}retrieve_"
                f"{RETRIEVAL_MODELS[0].replace('-','_')}_header_openai_small"
            )
            os.makedirs(SAVE_BASE_DIR, exist_ok=True)
            os.makedirs(f"{SAVE_BASE_DIR}/retrieval", exist_ok=True)

            results = run_retrieval_evaluation(
                dataset_path=DATASET_PATH,
                base_dir=SAVE_BASE_DIR,
                embedding_matrix=embedding_matrix_header,
                doc_names=doc_names_header,
                headers=headers,
                md5s=md5s,
                llm_models=RETRIEVAL_MODELS,
                openai_client=chatgpt_agent,
                perplexity_api_key=perplexity_api_key,
                top_k_values=[K_RERANK],
                k_retrieval=K_RETRIEVAL,
                embedder_id=EMBEDDER
            )

            all_results[f"header_k{K_RETRIEVAL}_top{K_RERANK}"] = results

    for K_RETRIEVAL in K_RETRIEVAL_POLICY:
        for K_RERANK in K_RERANK_LIST:

            SAVE_BASE_DIR = (
                f"{RESULTS_BASE}/"
                f"top{K_RERANK}_{K_RETRIEVAL}retrieve_"
                f"{RETRIEVAL_MODELS[0].replace('-','_')}_policy_openai_small"
            )
            os.makedirs(SAVE_BASE_DIR, exist_ok=True)
            os.makedirs(f"{SAVE_BASE_DIR}/retrieval", exist_ok=True)

            results = run_retrieval_evaluation_whole(
                dataset_path=DATASET_PATH,
                base_dir=SAVE_BASE_DIR,
                embedding_matrix=embedding_matrix_policy,
                doc_names=doc_names_policy,
                policies=policies,
                md5s=md5s,
                llm_models=RETRIEVAL_MODELS,
                openai_client=chatgpt_agent,
                perplexity_api_key=perplexity_api_key,
                top_k_values=[K_RERANK],
                k_retrieval=K_RETRIEVAL,
                embedder_id=EMBEDDER
            )

            all_results[f"policy_k{K_RETRIEVAL}_top{K_RERANK}"] = results

    print("\n[Header Results]")
    for key in sorted([k for k in all_results.keys() if k.startswith('header')]):
        print(f"\n{key}:")
        for model_topk, match_rate in all_results[key].items():
            print(f"  {model_topk}: {match_rate:.2%}")
    
    print("\n[Whole Policy Results]")
    for key in sorted([k for k in all_results.keys() if k.startswith('policy')]):
        print(f"\n{key}:")
        for model_topk, match_rate in all_results[key].items():
            print(f"  {model_topk}: {match_rate:.2%}")

    summary_data = []
    for key, res in all_results.items():
        for model_topk, match_rate in res.items():
            summary_data.append({
                'config': key,
                'model_topk': model_topk,
                'match_rate': match_rate
            })
    
    df_summary = pd.DataFrame(summary_data)
    summary_path = f"{RESULTS_BASE}/summary_all_configs.csv"
    df_summary.to_csv(summary_path, index=False)
    print(f" Summary saved to: {summary_path}")

if __name__ == "__main__":
    main()