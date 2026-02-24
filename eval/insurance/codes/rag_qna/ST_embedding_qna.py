import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from eval.insurance.codes.patient_policy_matching.load_policy import load_policies
from load_cases import load_unmatched_cases, load_matched_cases, load_correct_cases, load_incorrect_cases
from qna_execute import run_qna_for_cases
from qna_execute_baseline import run_baseline_qna_for_cases
from run_qna import clean_json_response, format_questions
from batch_qna_utils import USE_BATCH_QNA, get_batch_jsonl_path, submit_qna_batch

def main():
    TEST_MODE = False
    TEST_CASE_ID = "Case10917"

    if TEST_MODE:
        import batch_qna_utils
        batch_qna_utils.USE_BATCH_QNA = False
        print("TEST MODE: Batch disabled for immediate execution")

    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)
    
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset"
    DATASET_PATH = f"{BASE_DIR}/qna_free_text_sample.json"
    POLICY_FOLDER = f"{BASE_DIR}/insurance_policy"
    QUESTIONS_PATH = f"{BASE_DIR}/Insurance_Genetic_Testing_QA_Updated.json"
    INIT_RESULTS_BASE = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/patient_policy_match"
    RESULTS_BASE = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results/ST"
    os.makedirs(RESULTS_BASE, exist_ok=True)

    RETRIEVAL_MODEL = "gpt-5-mini"
    QNA_MODEL = "gpt-5-mini"

    if TEST_MODE:
        EXPERIMENTS = [{"type": "header", "k_retrieval": 10, "k_rerank": 1}]
    else:
        EXPERIMENTS = [
            # {"type": "header", "k_retrieval": 10, "k_rerank": 1},
            # {"type": "header", "k_retrieval": 10, "k_rerank": 3},
            # {"type": "header", "k_retrieval": 30, "k_rerank": 1},
            {"type": "header", "k_retrieval": 30, "k_rerank": 3},
        ]

    EXCLUDE_CASES = ["Case17595"]

    # unmatched_batches = []
    # matched_batches = []
    correct_batches = []
    incorrect_batches = []


    policies, md5s, headers = load_policies(POLICY_FOLDER)
    
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        case_ex = json.load(f)

    if TEST_MODE:
        case_ex = [c for c in case_ex if str(c["id"]) == TEST_CASE_ID] 
    else:
        case_ex = [c for c in case_ex if str(c["id"]) not in EXCLUDE_CASES]
    
    cid = {str(c["id"]): c for c in case_ex}
    
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    questions_list = questions_data["questions"]
    formatted_questions_text = format_questions(questions_list)

    for exp in EXPERIMENTS:
        exp_type = exp["type"] 
        K_RETRIEVAL = exp["k_retrieval"]
        K_RERANK = exp["k_rerank"]

        RERANK_DIR = (
                f"{INIT_RESULTS_BASE}/"
                f"top{K_RERANK}_{K_RETRIEVAL}retrieve_"
                f"{RETRIEVAL_MODEL.replace('-','_')}_{QNA_MODEL.replace('-','_')}_update"
            )

        RAG_SAVE_DIR = os.path.join(
            RESULTS_BASE,
            f"{RETRIEVAL_MODEL.replace('-','_')}_{QNA_MODEL.replace('-','_')}",
            "rag",
            f"{exp_type}_k{K_RETRIEVAL}_rerank{K_RERANK}"
        )
        os.makedirs(RAG_SAVE_DIR, exist_ok=True)
        
        BASELINE_SAVE_DIR = os.path.join(
            RESULTS_BASE,
            f"{RETRIEVAL_MODEL.replace('-','_')}_{QNA_MODEL.replace('-','_')}",
            "baseline",
            f"{exp_type}_k{K_RETRIEVAL}_rerank{K_RERANK}"
        )
        os.makedirs(BASELINE_SAVE_DIR, exist_ok=True)

        # unmatched_cases = load_unmatched_cases(
        #         RERANK_DIR,  
        #         rerank_model=RETRIEVAL_MODEL,
        #         top_k=K_RERANK,
        #         save_csv=True  
        # )

        # matched_cases = load_matched_cases(
        #         RERANK_DIR,
        #         rerank_model=RETRIEVAL_MODEL,
        #         top_k=K_RERANK,
        #         save_csv=True
        # )

        all_correct_cases = load_correct_cases(
                RERANK_DIR,
                rerank_model=RETRIEVAL_MODEL,
                top_k=K_RERANK,
                save_csv=True
        )

        all_incorrect_cases = load_incorrect_cases(
                RERANK_DIR,
                rerank_model=RETRIEVAL_MODEL,
                top_k=K_RERANK,
                save_csv=True
        )

        if TEST_MODE:
            matched_cases = [(c, d) for c, d in matched_cases if c == TEST_CASE_ID]
            unmatched_cases = [(c, d) for c, d in unmatched_cases if c == TEST_CASE_ID]
            all_correct_cases = [(c, d) for c, d in all_correct_cases if c == TEST_CASE_ID]
            all_incorrect_cases = [(c, d) for c, d in all_incorrect_cases if c == TEST_CASE_ID]
            print(f"TEST: Matched: {len(matched_cases)}, Unmatched: {len(unmatched_cases)}, All_Correct: {len(all_correct_cases)}, All_Incorrect: {len(all_incorrect_cases)}")

        # run_qna_for_cases(
        #         matches=unmatched_cases,
        #         case_by_id=cid,
        #         policies=policies,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=RAG_SAVE_DIR,  
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="unmatched",
        #         force_single_doc=False
        # )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #     batch_jsonl = get_batch_jsonl_path(RAG_SAVE_DIR, case_type="unmatched")
        #     if os.path.exists(batch_jsonl):
        #         log_dir = os.path.join(RAG_SAVE_DIR, "unmatched")
        #         os.makedirs(log_dir, exist_ok=True)
        #         bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #         unmatched_batches.append({
        #             "save_dir": RAG_SAVE_DIR,
        #             "batch_id": bid,
        #             "case_type": "unmatched",
        #             "mode": "rag",
        #             "exp_type": exp_type,
        #             "k_retrieval": K_RETRIEVAL,
        #             "k_rerank": K_RERANK,
        #             "qna_model": QNA_MODEL
        #         })
        #         print(f"[RAG Unmatched] Batch submitted: {bid}")

        # run_baseline_qna_for_cases(
        #         matches=unmatched_cases,
        #         case_by_id=cid,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=BASELINE_SAVE_DIR,
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="unmatched",
        #         force_single_doc=False
        #         )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #     batch_jsonl = get_batch_jsonl_path(BASELINE_SAVE_DIR, case_type="unmatched")
        #     if os.path.exists(batch_jsonl):
        #         log_dir = os.path.join(BASELINE_SAVE_DIR, "unmatched")
        #         os.makedirs(log_dir, exist_ok=True)
        #         bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #         unmatched_batches.append({
        #             "save_dir": BASELINE_SAVE_DIR,
        #             "batch_id": bid,
        #             "case_type": "unmatched",
        #             "mode": "baseline", 
        #             "exp_type": exp_type,
        #             "k_retrieval": K_RETRIEVAL,
        #             "k_rerank": K_RERANK,
        #             "qna_model": QNA_MODEL
        #         })
        #         print(f"[Baseline Unmatched] Batch submitted: {bid}")

        # run_qna_for_cases(
        #         matches=matched_cases,
        #         case_by_id=cid,
        #         policies=policies,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=RAG_SAVE_DIR,  
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="matched",
        #         force_single_doc=False
        # )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #         batch_jsonl = get_batch_jsonl_path(RAG_SAVE_DIR, case_type="matched")
        #         if os.path.exists(batch_jsonl):
        #             log_dir = os.path.join(RAG_SAVE_DIR, "matched")
        #             os.makedirs(log_dir, exist_ok=True)
        #             bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #             matched_batches.append({
        #                 "save_dir": RAG_SAVE_DIR,
        #                 "batch_id": bid,
        #                 "case_type": "matched",
        #                 "mode": "rag",
        #                 "exp_type": exp_type,
        #                 "k_retrieval": K_RETRIEVAL,
        #                 "k_rerank": K_RERANK,
        #                 "qna_model": QNA_MODEL
        #             })
        #             print(f"[RAG Matched] Batch submitted: {bid}")

        # run_baseline_qna_for_cases(
        #         matches=matched_cases,
        #         case_by_id=cid,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=BASELINE_SAVE_DIR,
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="matched",
        #         force_single_doc=False
        #         )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #     batch_jsonl = get_batch_jsonl_path(BASELINE_SAVE_DIR, case_type="matched")
        #     if os.path.exists(batch_jsonl):
        #         log_dir = os.path.join(BASELINE_SAVE_DIR, "matched")
        #         os.makedirs(log_dir, exist_ok=True)
        #         bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #         matched_batches.append({
        #             "save_dir": BASELINE_SAVE_DIR,
        #             "batch_id": bid,
        #             "case_type": "matched",
        #             "mode": "baseline", 
        #             "exp_type": exp_type,
        #             "k_retrieval": K_RETRIEVAL,
        #             "k_rerank": K_RERANK,
        #             "qna_model": QNA_MODEL
        #         })
        #         print(f"[Baseline Matched] Batch submitted: {bid}")

        run_qna_for_cases(
                matches=all_correct_cases,
                case_by_id=cid,
                policies=policies,
                retrieval_model=RETRIEVAL_MODEL,
                qna_model=QNA_MODEL,
                base_dir=RAG_SAVE_DIR,  
                K_RERANK=K_RERANK,
                formatted_questions=formatted_questions_text,
                openai_client=chatgpt_agent,
                clean_json_response=clean_json_response,
                case_type="all_correct",
                force_single_doc=True
        )

        if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
                batch_jsonl = get_batch_jsonl_path(RAG_SAVE_DIR, case_type="all_correct")
                if os.path.exists(batch_jsonl):
                    log_dir = os.path.join(RAG_SAVE_DIR, "all_correct")
                    os.makedirs(log_dir, exist_ok=True)
                    bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
                    correct_batches.append({
                        "save_dir": RAG_SAVE_DIR,
                        "batch_id": bid,
                        "case_type": "all_correct",
                        "mode": "rag",
                        "exp_type": exp_type,
                        "k_retrieval": K_RETRIEVAL,
                        "k_rerank": K_RERANK,
                        "qna_model": QNA_MODEL
                    })
                    print(f"[RAG All Correct] Batch submitted: {bid}")

        # run_baseline_qna_for_cases(
        #         matches=all_correct_cases,
        #         case_by_id=cid,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=BASELINE_SAVE_DIR,
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="all_correct",
        #         force_single_doc=True
        #         )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #     batch_jsonl = get_batch_jsonl_path(BASELINE_SAVE_DIR, case_type="all_correct")
        #     if os.path.exists(batch_jsonl):
        #         log_dir = os.path.join(BASELINE_SAVE_DIR, "all_correct")
        #         os.makedirs(log_dir, exist_ok=True)
        #         bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #         matched_batches.append({
        #             "save_dir": BASELINE_SAVE_DIR,
        #             "batch_id": bid,
        #             "case_type": "all_correct",
        #             "mode": "baseline", 
        #             "exp_type": exp_type,
        #             "k_retrieval": K_RETRIEVAL,
        #             "k_rerank": K_RERANK,
        #             "qna_model": QNA_MODEL
        #         })
        #         print(f"[Baseline All Correct] Batch submitted: {bid}")

        run_qna_for_cases(
                matches=all_incorrect_cases,
                case_by_id=cid,
                policies=policies,
                retrieval_model=RETRIEVAL_MODEL,
                qna_model=QNA_MODEL,
                base_dir=RAG_SAVE_DIR,  
                K_RERANK=K_RERANK,
                formatted_questions=formatted_questions_text,
                openai_client=chatgpt_agent,
                clean_json_response=clean_json_response,
                case_type="all_incorrect",
                force_single_doc=True
        )

        if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
                batch_jsonl = get_batch_jsonl_path(RAG_SAVE_DIR, case_type="all_incorrect")
                if os.path.exists(batch_jsonl):
                    log_dir = os.path.join(RAG_SAVE_DIR, "all_incorrect")
                    os.makedirs(log_dir, exist_ok=True)
                    bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
                    incorrect_batches.append({
                        "save_dir": RAG_SAVE_DIR,
                        "batch_id": bid,
                        "case_type": "all_incorrect",
                        "mode": "rag",
                        "exp_type": exp_type,
                        "k_retrieval": K_RETRIEVAL,
                        "k_rerank": K_RERANK,
                        "qna_model": QNA_MODEL
                    })
                    print(f"[RAG All Incorrect] Batch submitted: {bid}")

        # run_baseline_qna_for_cases(
        #         matches=all_incorrect_cases,
        #         case_by_id=cid,
        #         retrieval_model=RETRIEVAL_MODEL,
        #         qna_model=QNA_MODEL,
        #         base_dir=BASELINE_SAVE_DIR,
        #         K_RERANK=K_RERANK,
        #         formatted_questions=formatted_questions_text,
        #         openai_client=chatgpt_agent,
        #         clean_json_response=clean_json_response,
        #         case_type="all_incorrect",
        #         force_single_doc=True
        #         )

        # if USE_BATCH_QNA and QNA_MODEL.lower().startswith("gpt"):
        #     batch_jsonl = get_batch_jsonl_path(BASELINE_SAVE_DIR, case_type="all_incorrect")
        #     if os.path.exists(batch_jsonl):
        #         log_dir = os.path.join(BASELINE_SAVE_DIR, "all_incorrect")
        #         os.makedirs(log_dir, exist_ok=True)
        #         bid = submit_qna_batch(chatgpt_agent, batch_jsonl, log_dir=log_dir)
        #         matched_batches.append({
        #             "save_dir": BASELINE_SAVE_DIR,
        #             "batch_id": bid,
        #             "case_type": "all_incorrect",
        #             "mode": "baseline", 
        #             "exp_type": exp_type,
        #             "k_retrieval": K_RETRIEVAL,
        #             "k_rerank": K_RERANK,
        #             "qna_model": QNA_MODEL
        #         })
        #         print(f"[Baseline All Incorrect] Batch submitted: {bid}")              

    # unmatched_summary_path = f"{RESULTS_BASE}/batch_summary_unmatched_ST.json"
    # with open(unmatched_summary_path, "w", encoding="utf-8") as f:
    #     json.dump(unmatched_batches, f, indent=2, ensure_ascii=False)

    # matched_summary_path = f"{RESULTS_BASE}/batch_summary_matched_ST.json"
    # with open(matched_summary_path, "w", encoding="utf-8") as f:
    #     json.dump(matched_batches, f, indent=2, ensure_ascii=False)

    all_correct_summary_path = f"{RESULTS_BASE}/batch_summary_all_correct_ST.json"
    with open(all_correct_summary_path, "w", encoding="utf-8") as f:
        json.dump(correct_batches, f, indent=2, ensure_ascii=False)

    all_incorrect_summary_path = f"{RESULTS_BASE}/batch_summary_all_incorrect_ST.json"
    with open(all_incorrect_summary_path, "w", encoding="utf-8") as f:
        json.dump(incorrect_batches, f, indent=2, ensure_ascii=False)
if __name__ == "__main__":
    main()

    