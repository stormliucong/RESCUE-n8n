import os
import json
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
from load_unmatched_cases import load_unmatched_cases
from run_qna import run_qna, clean_json_response, format_questions, build_cached_prefix, build_qna_input_cached
from qna_execute import run_qna_for_matched_cases
from batch_qna_utils import USE_BATCH_QNA, get_batch_jsonl_path, submit_qna_batch

def main():
    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)
    
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset"
    DATASET_PATH = f"{BASE_DIR}/qna_free_text_sample.json"
    POLICY_FOLDER = f"{BASE_DIR}/insurance_policy"
    QUESTIONS_PATH = f"{BASE_DIR}/Insurance_Genetic_Testing_QA.json"

    K_RETRIEVAL_LIST = [10, 30]
    K_RERANK_LIST = [3]
    RETRIEVAL_MODELS = ["gpt-5-mini", "gpt-5"]
    QNA_MODELS = ["gpt-5-mini", "gpt-5"]
    EMBEDDER = "all-MiniLM-L6-v2"

    all_batches = []

    print("Loading policies...")
    policies, md5s, headers = load_policies(POLICY_FOLDER)

    print("Load samples")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        case_ex = json.load(f)
    cid = {str(c["id"]): c for c in case_ex}

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    questions_list = questions_data["questions"]
    formatted_questions_text = format_questions(questions_list)

    print("Creating embeddings...") 
    embeddings, doc_names, embedding_matrix = embed_policies_from_headers(headers=headers, md5s=md5s, cache_dir=BASE_DIR, embedder_id=EMBEDDER, cache_suffix="update" )

    for RETRIEVAL_MODEL in RETRIEVAL_MODELS:
        for QNA_MODEL in QNA_MODELS:
            for K_RETRIEVAL in K_RETRIEVAL_LIST:
                for K_RERANK in K_RERANK_LIST:

                    SAVE_BASE_DIR = (
                        "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/"
                        f"LLM_QnA/RAG/final/top{K_RERANK}_{K_RETRIEVAL}retrieve_{RETRIEVAL_MODEL.replace('-','_')}_{QNA_MODEL.replace('-','_')}_update"
                    )

                    unmatched_cases = load_unmatched_cases(SAVE_BASE_DIR, rerank_model=RETRIEVAL_MODEL, top_k=K_RERANK, save_csv=True)

                    run_qna_for_matched_cases(
                        matches=unmatched_cases,
                        case_by_id=cid,
                        policies=policies,
                        retrieval_model=RETRIEVAL_MODEL,
                        qna_model=QNA_MODEL,
                        base_dir=SAVE_BASE_DIR,
                        K_RERANK=K_RERANK,
                        formatted_questions=formatted_questions_text,
                        openai_client=chatgpt_agent,
                        perplexity_api_key=perplexity_api_key,
                        clean_json_response=clean_json_response,
                        case_type="unmatched"
                    )

                    if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
                        batch_jsonl_unmatched = get_batch_jsonl_path(SAVE_BASE_DIR, case_type="unmatched")
                        if os.path.exists(batch_jsonl_unmatched):
                            log_dir = os.path.join(SAVE_BASE_DIR, "qna_raw", "unmatched")
                            bid = submit_qna_batch(chatgpt_agent, batch_jsonl_unmatched, log_dir=log_dir)
                            all_batches.append({"save_dir": SAVE_BASE_DIR, "batch_id": bid, "case_type": "unmatched"})

    summary_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/final/batch_summary_unmatched.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_batches, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Submitted {len(all_batches)} QnA batches. Summary -> {summary_path}")

if __name__ == "__main__":
    main()