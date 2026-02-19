import os
import pandas as pd

def merge_all_qna_results(parent_dir, model_configs):
    '''merge all the qna_results.csv into one dataframe and save as csv'''
    
    rag_data = []
    baseline_data = []
    results_path = os.path.join(parent_dir, "results", "LLM_QnA", "RAG", "final")

    for config in model_configs:
        combo_folder = config["combo_folder"]
        rag_path = os.path.join(results_path, combo_folder, "qna_raw", "qna_results_rag.csv")
        if os.path.exists(rag_path):
            df = pd.read_csv(rag_path)
            df["top_k"] = config["top_k"]
            df["retrieval_count"] = config["retrieval_count"]
            df["combo_folder"] = combo_folder.replace("_update", "")
            df["retrieval_model"] = config["retrieval_model"]
            df["qna_model"] = config["qna_model"]
            
            rag_data.append(df)

        baseline_path = os.path.join(results_path, combo_folder, "qna_raw", "baseline", "qna_results_baseline.csv")
        if os.path.exists(baseline_path):
            df = pd.read_csv(baseline_path)
            df["top_k"] = config["top_k"]
            df["retrieval_count"] = config["retrieval_count"]
            df["combo_folder"] = combo_folder.replace("_update", "")
            df["retrieval_model"] = config["retrieval_model"]
            df["qna_model"] = config["qna_model"]

            baseline_data.append(df)    

    rag_df = None
    baseline_df = None
    
    if rag_data:
        rag_df = pd.concat(rag_data, ignore_index=True)
        rag_df.to_csv(os.path.join(results_path, "all_rag_matched_results_merged.csv"), index=False)

    if baseline_data:
        baseline_df = pd.concat(baseline_data, ignore_index=True)
        baseline_df.to_csv(os.path.join(results_path, "all_baseline_matched_results_merged.csv"), index=False)

    return rag_df, baseline_df


if __name__ == "__main__":
    parent_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance"

    top_k_values = [1, 3]
    retrieval_counts = [10, 30]
    retrieval_models = ["gpt-5-mini", "gpt-5"]
    qna_models = ["gpt-5-mini", "gpt-5"]

    model_configs = []

    for top_k in top_k_values:
        for ret_count in retrieval_counts:
            for ret_model in retrieval_models:
                for qna_model in qna_models:
                
                    ret_model_folder = ret_model.replace("-", "_")
                    qna_model_folder = qna_model.replace("-", "_")
                
                    combo_folder = f"top{top_k}_{ret_count}retrieve_{ret_model_folder}_{qna_model_folder}_update"
                
                    config = {
                        "combo_folder": combo_folder,
                        "top_k": top_k,
                        "retrieval_count": ret_count,
                        "retrieval_model": ret_model, 
                        "qna_model": qna_model  
                    }
                    model_configs.append(config)

    print(f"총 {len(model_configs)}개 조합:")
    for cfg in model_configs:
        print(f"  - {cfg['combo_folder']}")


    rag_df, baseline_df = merge_all_qna_results(parent_dir, model_configs)
