from calculate_match_rate import combine_match_rate

def combine_retrieval_results(base_dir, models=('gpt-5-mini',), top_k_values=(1, 3), output_filename="combined_match_rates.csv"):
    # Generate all model/top_k combinations
    pairs = []
    for model in models:
        for k in top_k_values:
            csv_path = f"{base_dir}/retrieval/{model.replace('-', '_')}/top{k}/matching_summary.csv"
            pairs.append((model, k, csv_path))
    
    # Combine results
    output_csv = f"{base_dir}/retrieval/{output_filename}"
    combine_match_rate(pairs, output_csv)
    print(f"Saved: {output_csv}")
    
    return output_csv

if __name__ == "__main__":
    import tempfile
    import os
    import pandas as pd
    import math

    # base_dir = tempfile.mkdtemp(prefix="retrieval_combine_")

    # os.makedirs(os.path.join(base_dir, "retrieval", "gpt_5_mini", "top1"), exist_ok=True)
    # os.makedirs(os.path.join(base_dir, "retrieval", "gpt_5_mini", "top3"), exist_ok=True)

    # pd.DataFrame({
    #     "case_id": ["C1","C2","C3","C4","C5"],
    #     "matched": [1, 0, 1, 0, 0],  
    # }).to_csv(os.path.join(base_dir, "retrieval", "gpt_5_mini", "top1", "matching_summary.csv"), index=False)

    # pd.DataFrame({
    #     "case_id": ["C1","C2","C3"],
    #     "matched": [0, 1, 1],            
    # }).to_csv(os.path.join(base_dir, "retrieval", "gpt_5_mini", "top3", "matching_summary.csv"), index=False)

    # out_csv = combine_retrieval_results(base_dir)
    # print("COMBINED CSV:", out_csv)
    # print(pd.read_csv(out_csv))

    # df = pd.read_csv(out_csv)
    # df1 = df[df["top_k"] == 1].reset_index(drop=True)
    # df2 = df[df["top_k"] == 3].reset_index(drop=True)

    # m1 = float(df1.loc[df1["top_k"] == 1, "match_rate"].iloc[0])
    # m2 = float(df2.loc[df2["top_k"] == 3, "match_rate"].iloc[0])
    # assert math.isclose(m1, 0.4)
    # assert math.isclose(m2, 2/3)

    # assert int(df1.loc[df1["top_k"] == 1, "matched_cases"].iloc[0]) == 2
    # assert int(df2.loc[df2["top_k"] == 3, "matched_cases"].iloc[0]) == 2
    # assert int(df1.loc[df1["top_k"] == 1, "total_cases"].iloc[0]) == 5
    # assert int(df2.loc[df2["top_k"] == 3, "total_cases"].iloc[0]) == 3

    experiments = [
        ("top1_10retrieve_gpt_5_mini_header_openai_small", 1, 10),
        ("top3_10retrieve_gpt_5_mini_header_openai_small", 3, 10),
        ("top1_30retrieve_gpt_5_mini_header_openai_small", 1, 30),
        ("top3_30retrieve_gpt_5_mini_header_openai_small", 3, 30),
        ("top1_10retrieve_gpt_5_mini_policy_openai_small", 1, 10),
        ("top3_10retrieve_gpt_5_mini_policy_openai_small", 3, 10)
    ]
    
    base = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"
    
    all_pairs = []
    for folder, top_k, retrieval_count in experiments:
        csv_path = f"{base}/{folder}/retrieval/gpt_5_mini/top{top_k}/matching_summary.csv"
        all_pairs.append(("gpt-5-mini", "gpt-5-mini", retrieval_count, top_k, csv_path))
    
    output_csv = f"{base}/combined_openai_match_rates.csv"
    combine_match_rate(all_pairs, output_csv)
    print(f"✅ Saved: {output_csv}")