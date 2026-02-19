from load_inputs import load_inputs
from run_qna_File_Agent import QnAExecutorWithPDF
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

def main():
    TEST_MODE = True
    TEST_CASE_ID = "Case10917"
    TEST_MODEL = "gpt-5-mini"

    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    chatgpt_agent = OpenAI(api_key=openai_api_key)

    questions_file_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/Insurance_Genetic_Testing_QA.json"
    with open(questions_file_path, "r") as f:
        questions_data = json.load(f)
    questions_list = questions_data["questions"]

    case_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/qna_free_text_sample.json"
    truth_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/final_ground_truth.json"

    cases, ground_truth = load_inputs(case_path, truth_path)
    
    if TEST_MODE:
        cases = [c for c in cases if str(c.get("id", "")) == TEST_CASE_ID]
        models = [TEST_MODEL]
    else:
        EXCLUDE_CASES = ["Case17595"]
        cases = [c for c in cases if str(c.get("id", "")) not in EXCLUDE_CASES]
        models = ["gpt-4o", "gpt-5-mini", "gpt-5"]
    
    RESULTS_BASE = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results/File_Agent"
    os.makedirs(RESULTS_BASE, exist_ok=True)

    for model in models:

        model_dir = os.path.join(RESULTS_BASE, model)
        os.makedirs(model_dir, exist_ok=True)

        executor = QnAExecutorWithPDF(
            questions_list=questions_list,
            llm_model=model,
            openai_api_key=openai_api_key,
            save_base_dir=model_dir
        )

        if TEST_MODE:
            for case in cases:
                result = executor.run_qna_with_pdf(case)
                if result:
                    print(f"Completed: {case['id']}")

        else:
            jsonl_path = executor.prepare_batch_for_cases(cases)
            print(f"Batch JSONL created: {jsonl_path}")
    
            batch_id = executor.submit_batch(jsonl_path)
            print(f"Batch submitted with ID: {batch_id}")

if __name__ == "__main__":
    main()