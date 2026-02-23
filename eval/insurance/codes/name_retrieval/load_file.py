import os
import pandas as pd
import json

def load_ground_truth(csv_path):
    '''Load ground truth provider list from CSV file'''
    df = pd.read_csv(csv_path)
    pr_list = df['Providers'].dropna().str.strip().tolist()
    print(len(pr_list))
    return pr_list

def load_result(base_dir, iteration, prompt_type, model_name="gpt-4o"):
    '''Load provider list from experiment result files (JSON or CSV)'''
    base_path = f"{base_dir}/iteration_{iteration}/{model_name}/{prompt_type}"
    
    # JSON attempt (gpt-5-mini)
    json_file = f"{base_path}/result.json"
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)['parsed_data']['Providers']
    
    # CSV attempt (gpt-4o, perplexity)
    csv_file = f"{base_path}/provider.csv"
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        return df['Providers'].dropna().str.strip().tolist()
    
    print(f"File not found: {base_path}")
    return []