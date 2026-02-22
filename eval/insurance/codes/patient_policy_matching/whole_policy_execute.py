import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from load_policy import load_policies, calculate_pdf_md5
from embedding_policies import embed_policies_from_headers
from rerank_whole import rerank_whole_policies
from calculate_match_rate import calculate_match_rate
from md5_matching import md5_match_by_rerank_order
from retrieve_candidates import retrieve_candidates
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

    save_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/final/whole_policy"
    os.makedirs(save_dir, exist_ok=True)

    policies, md5s, headers = load_policies(POLICY_FOLDER)

    embeddings, doc_names, embedding_matrix = embed_policies_from_headers(
        headers=policies,
        md5s=md5s,
        cache_dir= save_dir,
        embedder_id="all-MiniLM-L6-v2",
        cache_suffix="whole_policy"
    )

    run_retrieval_evaluation_whole(
        dataset_path=DATASET_PATH,
        base_dir=save_dir,
        embedding_matrix=embedding_matrix,
        doc_names=doc_names,
        policies=policies,
        md5s=md5s,
        openai_client=chatgpt_agent, 
        perplexity_api_key=perplexity_api_key,
        llm_models=['gpt-5-mini'],
        top_k_values= [1, 3],
        k_retrieval=10,
        embedder_id="all-MiniLM-L6-v2"
    )

if __name__ == "__main__":
    main()