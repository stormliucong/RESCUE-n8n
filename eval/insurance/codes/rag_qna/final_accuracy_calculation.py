import pandas as pd
import json

def calculate_accuracy(results_csv_path, ground_truth_json_path, output_csv_path):
    """
    Calculate accuracy metrics for experimental results
    
    Adds the following columns:
    - Basic accuracy (all 9 questions)
    - Adjusted accuracy (excluding "Not Specified" in both ground truth and prediction)
    - QuestionUnclear & Not Answerable counts
    """
    df = pd.read_csv(results_csv_path)
    
    with open(ground_truth_json_path, 'r') as f:
        ground_truth = json.load(f)
    
    questions = ["Q0", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"]
    
    correct_list = []
    total_list = []
    accuracy_list = []
    wrong_questions_list = []
    wrong_predictions_list = []
    ground_truth_list = []
    
    adjusted_correct_list = []
    adjusted_total_list = []
    adjusted_accuracy_list = []
    adjusted_wrong_questions_list = []
    adjusted_wrong_predictions_list = []
    adjusted_ground_truth_list = []
    
    unclear_count_list = []
    unclear_questions_list = []
    not_answerable_count_list = []
    not_answerable_questions_list = []

    for idx, row in df.iterrows():
        case_id = row['case_id']
        
        gt = ground_truth.get(case_id)
        
        if gt is None:
            correct_list.append(None)
            total_list.append(None)
            accuracy_list.append(None)
            wrong_questions_list.append(None)
            ground_truth_list.append(None)
            adjusted_correct_list.append(None)
            adjusted_total_list.append(None)
            adjusted_accuracy_list.append(None)
            adjusted_wrong_questions_list.append(None)
            adjusted_ground_truth_list.append(None)
            unclear_count_list.append(0)
            unclear_questions_list.append('')
            not_answerable_count_list.append(0)
            not_answerable_questions_list.append('')
            continue
        
        basic_correct = 0
        basic_total = 9
        basic_wrong_qs = []
        basic_pred_answers = []
        basic_gt_answers = []
        
        adjusted_correct = 0
        adjusted_total = 0
        adjusted_wrong_qs = []
        adjusted_pred_answers = []
        adjusted_gt_answers = []
        
        unclear_count = 0
        unclear_qs = []
        not_answerable_count = 0
        not_answerable_qs = []
        
        for q in questions:
            predicted_answer = str(row.get(q + '_answer', '')).strip()
            true_answer = str(gt.get(q, '')).strip()
            
            if predicted_answer == true_answer:
                basic_correct += 1
            else:
                basic_wrong_qs.append(q)
                basic_pred_answers.append(f"{q}:{predicted_answer}")
                basic_gt_answers.append(f"{q}:{true_answer}")
            
            excluded_answers = ["Not Specified", "Question Unclear", "Not Answerable"]
            if true_answer not in excluded_answers and predicted_answer not in excluded_answers:
                adjusted_total += 1
                if predicted_answer == true_answer:
                    adjusted_correct += 1
                else:
                    adjusted_wrong_qs.append(q)
                    adjusted_pred_answers.append(f"{q}:{predicted_answer}")
                    adjusted_gt_answers.append(f"{q}:{true_answer}")
            
            if predicted_answer == "Question Unclear":
                unclear_count += 1
                unclear_qs.append(q)
            
            if predicted_answer == "Not Answerable":
                not_answerable_count += 1
                not_answerable_qs.append(q)
        
        basic_accuracy = 100 * basic_correct / basic_total if basic_total > 0 else 0
        adjusted_accuracy = 100 * adjusted_correct / adjusted_total if adjusted_total > 0 else 0
        
        correct_list.append(basic_correct)
        total_list.append(basic_total)
        accuracy_list.append(basic_accuracy)
        wrong_questions_list.append(','.join(basic_wrong_qs) if basic_wrong_qs else '')
        wrong_predictions_list.append('|'.join(basic_pred_answers) if basic_pred_answers else '')
        ground_truth_list.append('|'.join(basic_gt_answers) if basic_gt_answers else '')
        
        adjusted_correct_list.append(adjusted_correct)
        adjusted_total_list.append(adjusted_total)
        adjusted_accuracy_list.append(adjusted_accuracy)
        adjusted_wrong_questions_list.append(','.join(adjusted_wrong_qs) if adjusted_wrong_qs else '')
        adjusted_wrong_predictions_list.append('|'.join(adjusted_pred_answers) if adjusted_pred_answers else '')
        adjusted_ground_truth_list.append('|'.join(adjusted_gt_answers) if adjusted_gt_answers else '')
        
        unclear_count_list.append(unclear_count)
        unclear_questions_list.append(','.join(unclear_qs) if unclear_qs else '')
        not_answerable_count_list.append(not_answerable_count)
        not_answerable_questions_list.append(','.join(not_answerable_qs) if not_answerable_qs else '')
    
    print("Adding new columns...")
    df['correct'] = correct_list
    df['total'] = total_list
    df['accuracy'] = accuracy_list
    df['wrong_questions'] = wrong_questions_list
    df['wrong_predictions'] = wrong_predictions_list
    df['ground_truth'] = ground_truth_list
    
    df['adjusted_correct'] = adjusted_correct_list
    df['adjusted_total'] = adjusted_total_list
    df['adjusted_accuracy'] = adjusted_accuracy_list
    df['adjusted_wrong_questions'] = adjusted_wrong_questions_list
    df['adjusted_wrong_predictions'] = adjusted_wrong_predictions_list
    df['adjusted_ground_truth'] = adjusted_ground_truth_list
    
    df['unclear_count'] = unclear_count_list
    df['unclear_questions'] = unclear_questions_list
    df['not_answerable_count'] = not_answerable_count_list
    df['not_answerable_questions'] = not_answerable_questions_list
    
    columns_to_remove = ['input_tokens', 'output_tokens', 'total_tokens', 'md5_hash']
    df = df.drop(columns=columns_to_remove, errors='ignore')
    
    df.to_csv(output_csv_path, index=False)
    print(f"Done! Saved {len(df)} rows.")
    
    return df


# Main execution
if __name__ == "__main__":
    results_csv = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results/final_all_results_combined.csv"
    ground_truth_json = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/final_ground_truth.json"
    output_csv = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results/final_results_with_accuracy_updated.csv"
    
    df = calculate_accuracy(results_csv, ground_truth_json, output_csv)
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Mean Basic Accuracy: {df['accuracy'].mean():.2f}%")
    print(f"Mean Adjusted Accuracy: {df['adjusted_accuracy'].mean():.2f}%")
    print(f"Total Unclear responses: {df['unclear_count'].sum()}")
    print(f"Total Not Answerable responses: {df['not_answerable_count'].sum()}")
