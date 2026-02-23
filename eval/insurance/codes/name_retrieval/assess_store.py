import os
import pandas as pd
from openai import OpenAI
from load_file import load_ground_truth, load_result
from match_function import exact_match, regex_match, llm_evaluate

def evaluate_single_iteration(base_dir, ground_truth, openai_client, 
                             prompt_type, iteration, log_dir, 
                             experiment_model, evaluator_model="gpt-4o"):
    '''evaluate one iteration of one prompt type'''

    predicted = load_result(base_dir, iteration, prompt_type, experiment_model) 
    
    
    ep, er = exact_match(predicted, ground_truth)
    rp, rr = regex_match(predicted, ground_truth)
    llm_result = llm_evaluate(predicted, ground_truth, openai_client, 
                             log_dir, evaluator_model)
    
    return {
        'prompt_type': prompt_type,
        'iteration': iteration,
        'total_retrieved': len(predicted),
        'exact_precision': ep,
        'exact_recall': er,
        'regex_precision': rp,
        'regex_recall': rr,
        'llm_precision': llm_result['precision'],
        'llm_recall': llm_result['recall'],
        'llm_details': {
            'common': llm_result['common_providers'],
            'missing': llm_result['missing_providers'],
            'extra': llm_result['extra_providers']
        }
    }

def evaluate_all_experiments(base_dir, ground_truth_path, openai_api_key, 
                            log_dir, experiment_model, evaluator_model="gpt-4o"): 
    """all iteration + average calculation"""
    
    ground_truth = load_ground_truth(ground_truth_path)
    client = OpenAI(api_key=openai_api_key)
    
    all_results = []
    
    for prompt_type in ['baseline', 'explicit']:
        print(f"\nEvaluating {prompt_type}...")
        
        iteration_results = []
        for i in range(1, 4):
            print(f"  Iteration {i}...")
            result = evaluate_single_iteration(base_dir, ground_truth, client, 
                                   prompt_type, i, log_dir, 
                                   experiment_model, evaluator_model)
            all_results.append(result)
            iteration_results.append(result)
        
        avg_result = {
            'prompt_type': prompt_type,
            'iteration': 'Average',
            'total_retrieved': sum(r['total_retrieved'] for r in iteration_results) / 3,
            'exact_precision': sum(r['exact_precision'] for r in iteration_results) / 3,
            'exact_recall': sum(r['exact_recall'] for r in iteration_results) / 3,
            'regex_precision': sum(r['regex_precision'] for r in iteration_results) / 3,
            'regex_recall': sum(r['regex_recall'] for r in iteration_results) / 3,
            'llm_precision': sum(r['llm_precision'] for r in iteration_results) / 3,
            'llm_recall': sum(r['llm_recall'] for r in iteration_results) / 3,
            'llm_details': None 
        }
        all_results.append(avg_result)
    
    return all_results

def save_results(results, output_dir, experiment_model, evaluator_model):
    """store results in CSV"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    processed_results = []
    for r in results:
        result_copy = {k: v for k, v in r.items() if k != 'llm_details'}
        if r.get('llm_details'):  
            result_copy['llm_common'] = '|'.join(r['llm_details']['common'])
            result_copy['llm_missing'] = '|'.join(r['llm_details']['missing'])
            result_copy['llm_extra'] = '|'.join(r['llm_details']['extra'])
        else:  
            result_copy['llm_common'] = ''
            result_copy['llm_missing'] = ''
            result_copy['llm_extra'] = ''
        
        processed_results.append(result_copy)
    
    df = pd.DataFrame(processed_results)

    df = df[['prompt_type', 'iteration', 'total_retrieved', 
             'exact_precision', 'exact_recall',
             'regex_precision', 'regex_recall', 
             'llm_precision', 'llm_recall',
             'llm_common', 'llm_missing', 'llm_extra']]
    
    df.columns = [
        'Prompt Type', 'Iteration', 'Total Retrieved',
        'Exact Match Precision (%)', 'Exact Match Recall (%)',
        'Regex Match Precision (%)', 'Regex Match Recall (%)',
        'LLM Match Precision (%)', 'LLM Match Recall (%)',
        'LLM Common Providers', 'LLM Missing Providers', 'LLM Extra Providers'
    ]
    
    df['Total Retrieved'] = df['Total Retrieved'].round(2)
    for col in df.columns[3:9]: 
        df[col] = df[col].round(2)
    

    filename = f"{experiment_model.replace('-', '_')}_eval_by_{evaluator_model.replace('-', '_')}.csv"
    csv_path = os.path.join(output_dir, filename)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"\n✓ CSV saved: {csv_path}")

    return df, csv_path