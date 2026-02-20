import os
import pandas as pd

def merge_results(result_base_dir, assessment_output, links_output):
    '''Merge results from multiple iterations, models, prompt types, and payers into consolidated CSV files'''
    assessment_results = []
    links_results = []
    
    for iteration in range(1, 4):
        for model in ["gpt-4o", "gpt-5-mini"]:
            for prompt_type in ["baseline", "keyword", "verified"]:
                for payer in ["United Healthcare", "Aetna", "Cigna", "Blue Cross and Blue Shield Federal Employee Program"]:
                    exp_dir = os.path.join(result_base_dir, f"iteration_{iteration}", model, prompt_type, payer.replace(" ", "_"))
                    
                    assessment_csv = os.path.join(exp_dir, "md5_comparison_results.csv")
                    if os.path.exists(assessment_csv):
                        df = pd.read_csv(assessment_csv)
                        df['model'] = model
                        df['prompt_type'] = prompt_type
                        df['iteration'] = iteration
                        assessment_results.append(df)
                    
                    links_csv = os.path.join(exp_dir, "links_summary.csv")
                    if os.path.exists(links_csv):
                        df = pd.read_csv(links_csv)
                        df['model'] = model
                        df['prompt_type'] = prompt_type
                        df['iteration'] = iteration
                        links_results.append(df)
    
    pd.concat(assessment_results, ignore_index=True).to_csv(assessment_output, index=False)
    pd.concat(links_results, ignore_index=True).to_csv(links_output, index=False)