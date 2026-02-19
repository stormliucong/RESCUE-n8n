import os
import json
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
from dotenv import load_dotenv
from openai import OpenAI
from run_qna_baseline import run_baseline_qna, build_baseline_qna_input_cached, build_baseline_cached_prefix, format_questions, clean_json_response
from load_matched_cases import load_matched_cases
from qna_execute_baseline import run_baseline_qna_for_matched_cases
from batch_qna_utils import USE_BATCH_QNA, get_batch_jsonl_path, submit_qna_batch

def main():
    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)
    
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset"
    DATASET_PATH = f"{BASE_DIR}/qna_free_text_sample.json"
    QUESTIONS_PATH = f"{BASE_DIR}/Insurance_Genetic_Testing_QA.json"

    K_RETRIEVAL_LIST = [10, 30]
    K_RERANK_LIST = [1, 3]
    RETRIEVAL_MODELS = ["gpt-5-mini", "gpt-5"]
    QNA_MODELS = ["gpt-5-mini", "gpt-5"]

    all_batches = []

    print("Load samples")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        case_ex = json.load(f)
    cid = {str(c["id"]): c for c in case_ex}

    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    questions_list = questions_data["questions"]
    formatted_questions_text = format_questions(questions_list)

    for RETRIEVAL_MODEL in RETRIEVAL_MODELS:
        for QNA_MODEL in QNA_MODELS:
            for K_RETRIEVAL in K_RETRIEVAL_LIST:
                for K_RERANK in K_RERANK_LIST:

                    SAVE_BASE_DIR = (
                        "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/"
                        f"LLM_QnA/RAG/final/top{K_RERANK}_{K_RETRIEVAL}retrieve_{RETRIEVAL_MODEL.replace('-','_')}_{QNA_MODEL.replace('-','_')}_update"
                    )
                    
                    matched_cases = load_matched_cases(SAVE_BASE_DIR, rerank_model=RETRIEVAL_MODEL, top_k=K_RERANK)

                    run_baseline_qna_for_matched_cases(
                        matches=matched_cases,
                        case_by_id=cid,
                        retrieval_model=RETRIEVAL_MODEL,
                        qna_model=QNA_MODEL,
                        base_dir=SAVE_BASE_DIR,
                        K_RERANK=K_RERANK,
                        formatted_questions=formatted_questions_text,
                        openai_client=chatgpt_agent,
                        perplexity_api_key=perplexity_api_key,
                        clean_json_response=clean_json_response
                    )

                    if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
                        batch_jsonl = get_batch_jsonl_path(SAVE_BASE_DIR)
                        if os.path.exists(batch_jsonl):
                            log_dir = os.path.join(SAVE_BASE_DIR, "qna_raw")
                            bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
                            all_batches.append({"save_dir": SAVE_BASE_DIR, "batch_id": bid})

    summary_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/final/baseline_batch_summary.json"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_batches, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Submitted {len(all_batches)} QnA batches. Summary -> {summary_path}")

if __name__ == "__main__":
    main()