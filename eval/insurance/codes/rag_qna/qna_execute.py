import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from eval.insurance.codes.patient_policy_matching.load_policy import load_policies
from eval.insurance.codes.patient_policy_matching.embedding_policies import embed_policies_from_headers
from eval.insurance.codes.patient_policy_matching.retrieve_candidates import retrieve_candidates
from eval.insurance.codes.patient_policy_matching.rerank_policies import rerank_policies
from eval.insurance.codes.patient_policy_matching.md5_matching import md5_match_by_rerank_order
from load_cases import load_matched_cases
from run_qna import run_qna, clean_json_response, format_questions, build_cached_prefix, build_qna_input_cached
import batch_qna_utils
from batch_qna_utils import enqueue_qna_batch_line, get_batch_jsonl_path, submit_qna_batch

path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
load_dotenv(dotenv_path=os.path.join(path, ".env"))
openai_api_key = os.getenv("OPEN_AI_API_KEY")
chatgpt_agent = OpenAI(api_key=openai_api_key)


def run_qna_for_cases(
        matches, 
        case_by_id, 
        policies, 
        retrieval_model, 
        qna_model, 
        base_dir, 
        K_RERANK, 
        formatted_questions, 
        openai_client, 
        clean_json_response,
        case_type="matched",
        force_single_doc=False):
    """Run Q&A for multiple cases (matched or unmatched)."""

    cached_prefix = build_cached_prefix(formatted_questions)
    qna_out_dir = os.path.join(base_dir, case_type)
    os.makedirs(qna_out_dir, exist_ok=True)

    outputs = []

    for item in matches:
        cid = None  
        policy_name = None

        try:
            if force_single_doc or K_RERANK == 1:
                cid, policy_name = item
                policy_text = policies.get(policy_name, "")
                print(f"Case {cid}: Single doc ({policy_name}): Policy: {policy_text[:100]}")
            else:
                cid, policy_names = item
                policy_texts = [policies.get(name, "") for name in policy_names if policies.get(name, "")]
                policy_text = "\n\n---DOCUMENT SEPARATOR---\n\n".join(policy_texts)
                policy_name = f"combined_{len(policy_names)}_docs"
                print(f"Case {cid}: Combined {len(policy_names)} docs")
                print(f"Document separators found: {policy_text.count('---DOCUMENT SEPARATOR---')}")
                
            if cid not in case_by_id:
                print(f"[SKIP] {cid}: Not in dataset")
                continue
            
            patient_info_text = case_by_id[cid]["patient_info"]

            if batch_qna_utils.USE_BATCH_QNA and qna_model.lower().startswith("gpt"):
                qna_input_text = build_qna_input_cached(
                    patient_info=patient_info_text,
                    policy_name=policy_name,
                    policy_text=policy_text,
                    cached_prefix=cached_prefix
                )

                jsonl_path = get_batch_jsonl_path(base_dir, case_type=case_type)
                custom = f"{cid}|qna|{case_type}|retr{K_RERANK}|{retrieval_model}|{qna_model}"
                enqueue_qna_batch_line(custom_id=custom, model=qna_model, input_text=qna_input_text, jsonl_path=jsonl_path)

                outputs.append({
                    "case_id": cid,
                    "policy": policy_name,
                    "queued": True
                })
                continue
        
            result_json = run_qna(
                patient_info=patient_info_text,
                policy_name=policy_name,
                policy_text=policy_text,
                case_id=cid,
                qna_model=qna_model,
                cached_prefix=cached_prefix,
                openai_client=openai_client,
                save_dir=qna_out_dir,
                clean_json_response_fn=clean_json_response
            )
            out_path = os.path.join(qna_out_dir, f"{cid}_qna.json")
            outputs.append({
                    "case_id": cid, 
                    "policy": policy_name, 
                    "output_path": out_path,
                    "result": result_json
            })
        except Exception as e:
            outputs.append({
                "case_id": cid or "unknown", 
                "policy": policy_name or "unknown",
                "error": str(e)
            })

    return outputs

if __name__ == "__main__":
    import batch_qna_utils
    batch_qna_utils.USE_BATCH_QNA = True 

    base_dir="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset"
    dataset_path="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/sample_qna_free_text.json"
    folder = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_answer_real"
    save_dir="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/toy_fin"
    os.makedirs(save_dir, exist_ok=True)
    
    policies, md5s, headers = load_policies(folder)
    embeddings, doc_names, embedding_matrix = embed_policies_from_headers(
        headers=headers,
        md5s=md5s,
        cache_dir=save_dir,
        embedder_id="all-MiniLM-L6-v2"
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        case_ex = json.load(f)
    case_by_id = {str(c["id"]): c for c in case_ex[:3]}
    
    K_RERANK = 1
    K_RETRIEVAL = 3
    retrieval_model = "gpt-5-mini"
    qna_model = "gpt-5-mini"
    os.makedirs(save_dir, exist_ok=True)

    for case in case_ex[:2]:
        cid = str(case["id"])
        query_text = case["patient_info"]
        expected_md5 = case["expected_md5"]

        cands = retrieve_candidates(
            vecs=embedding_matrix,
            names=doc_names,
            query_text=query_text,
            doc_texts=headers,               
            embedder_id="all-MiniLM-L6-v2",
            vecs_normalized=True,
            k=K_RETRIEVAL
        )

        order = rerank_policies(
                patient_info=query_text,
                candidates=cands,
                llm_model=retrieval_model,
                openai_client=chatgpt_agent,
                save_dir=save_dir,
                case_id=cid,
                top_k=K_RERANK
            )

        matched_name, matched, llm_rank, top_k_docs = md5_match_by_rerank_order(
            candidates=cands,
            order=order,
            md5s=md5s,
            expected_md5=expected_md5,
            save_dir=save_dir,
            case_id=cid,
            retrieval_model=retrieval_model,
            top_k=K_RERANK,
            embedding_matrix=embedding_matrix,
            doc_names=doc_names, 
            query_text=query_text
        )

    matches = load_matched_cases(save_dir, rerank_model=retrieval_model, top_k=K_RERANK)

    questions_file_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/Insurance_Genetic_Testing_QA.json"
    with open(questions_file_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    questions_list = questions_data["questions"]
    formatted_questions_text = format_questions(questions_list)

    outs = run_qna_for_cases(
        matches=matches,
        case_by_id=case_by_id,
        policies=policies,
        retrieval_model=retrieval_model,
        qna_model=qna_model,
        base_dir=save_dir,
        K_RERANK=K_RERANK,
        formatted_questions=formatted_questions_text,
        openai_client=chatgpt_agent,
        clean_json_response=clean_json_response
    )
    print(f"QnA outputs: {outs}")
    print("Q&A process completed.")

    if batch_qna_utils.USE_BATCH_QNA:
        jsonl_path = get_batch_jsonl_path(save_dir)
        if os.path.exists(jsonl_path):
            log_dir = os.path.join(save_dir, "qna_raw") 
            submit_qna_batch(chatgpt_agent, jsonl_path, log_dir)
            print("batch submission completed!")

