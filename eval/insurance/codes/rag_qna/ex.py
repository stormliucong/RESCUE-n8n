import pandas as pd

sentence = pd.read_csv("/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/all_sentence_unmatched_results_merged.csv")
baseline = pd.read_csv("/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/all_baseline_results_merged.csv")

# print("\nCombo counts:")
# print(sentence.groupby('combo_folder')['case_id'].count().sort_index())

# print("\n\n=== Baseline ===")
# print(f"Total: {len(baseline)}, Unique cases: {baseline['case_id'].nunique()}")
# print("\nCombo counts:")
# print(baseline.groupby('combo_folder')['case_id'].count().sort_index())

# # 케이스 차이
# sentence_cases = set(sentence['case_id'].unique())
# baseline_cases = set(baseline['case_id'].unique())

# only_sentence = sentence_cases - baseline_cases
# only_baseline = baseline_cases - sentence_cases

# print(f"\n\n=== Differences ===")
# print(f"Only in sentence: {len(only_sentence)} - {sorted(only_sentence)}")
# print(f"Only in baseline: {len(only_baseline)} - {sorted(only_baseline)}")

for combo in sentence['combo_folder'].unique():
    s_df = sentence[sentence['combo_folder'] == combo]
    b_df = baseline[baseline['combo_folder'] == combo]
    
    s_dup = s_df[s_df.duplicated(subset=['case_id'], keep=False)]
    b_dup = b_df[b_df.duplicated(subset=['case_id'], keep=False)]
    
    if len(s_dup) > 0 or len(b_dup) > 0:
        print(f"\n{combo}:")
        print(f"  Sentence duplicates: {len(s_dup)}")
        print(f"  Baseline duplicates: {len(b_dup)}")
        if len(s_dup) > 0:
            print(f"    Cases: {s_dup['case_id'].unique()}")