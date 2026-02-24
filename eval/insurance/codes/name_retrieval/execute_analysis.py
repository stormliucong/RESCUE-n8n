import os
from dotenv import load_dotenv
from assess_store import evaluate_all_experiments, save_results

load_dotenv('/home/cptaswadu/new-rescue/RESCUE-n8n/.env')

BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval/final"
GT_PATH = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/In-Network_Providers_Update.csv"
OUTPUT_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval/evaluation_results"
LOG_DIR = OUTPUT_DIR
API_KEY = os.getenv("OPEN_AI_API_KEY")
EXPERIMENT_MODEL = ["perplexity", "gpt-4o", "gpt-4o-oct", "gpt-5-mini"]      
EVALUATOR_MODEL = ["gpt-4o", "gpt-5-mini"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

for exp_model in EXPERIMENT_MODEL:
    for eval_model in EVALUATOR_MODEL:
        print(f"\nAssessing: {exp_model} (By: {eval_model})")
        try:
            results = evaluate_all_experiments(BASE_DIR, GT_PATH, API_KEY, LOG_DIR, 
                                               exp_model, eval_model)
            df, csv_path = save_results(results, OUTPUT_DIR, exp_model, eval_model)
            print(f"Success: {csv_path}")
        except Exception as e:
            print(f"Failure: {e}")