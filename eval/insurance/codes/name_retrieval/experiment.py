import os
from dotenv import load_dotenv
from openai import OpenAI
from prompt import prompt_functions
from name_retrieval import query_llm_for_providers, clean_json_response

def main():
    BASE_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval/final"
    os.makedirs(BASE_DIR, exist_ok=True)

    DOTENV_PATH = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(DOTENV_PATH, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    openai_client = OpenAI(api_key=openai_api_key)

    prompt_types = ["baseline", "explicit"]
    
    for prompt_type in prompt_types:
        for i in range(1, 4):
            result = query_llm_for_providers(
                prompt_type=prompt_type,
                model="openai",
                openai_model="gpt-4o",
                iteration=i,
                base_output_dir=BASE_DIR,
                openai_client=openai_client,
                perplexity_api_key=perplexity_api_key,
                max_retries=3
            )
            print(f"{prompt_type} - Iteration {i} completed")

if __name__ == "__main__":
    main()