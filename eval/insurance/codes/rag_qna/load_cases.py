import os
import pandas as pd

# ========== Helper Functions ==========

def _get_folder_path(base_dir, rerank_model, top_k):
    """Generate folder path"""
    return os.path.join(base_dir, "retrieval", rerank_model.replace("-", "_"), f"top{int(top_k)}")

def _save_results_to_csv(result, top_k, save_path):
    """Save results to CSV"""
    if top_k == 1:
        df = pd.DataFrame(result, columns=['case_id', 'doc_names'])
    else:
        df_data = [(case_id, "|".join(docs)) for case_id, docs in result]
        df = pd.DataFrame(df_data, columns=['case_id', 'doc_names'])
    
    df.to_csv(save_path, index=False, encoding='utf-8', quoting=1)
    print(f"Saved to: {save_path}")


# ========== Main Functions ==========

def load_matched_cases(base_dir, rerank_model, top_k, save_csv=True, save_dir=None):
    """
    Load matched cases (matched=1) with top-k documents
    
    Args:
        base_dir: Base directory containing retrieval results
        rerank_model: Reranking model name
        top_k: Number of top documents to retrieve
        save_csv: Whether to save results as CSV
        save_dir: Directory to save CSV (default: same as data folder)
    
    Returns:
        top_k=1: [(case_id, doc_name), ...]
        top_k>1: [(case_id, [doc1, doc2, ...]), ...]
    """
    folder = _get_folder_path(base_dir, rerank_model, top_k)
    
    if top_k == 1:
        # Get matched=1 cases from matching_summary.csv
        csv_path = os.path.join(folder, "matching_summary.csv")
        df = pd.read_csv(csv_path)
        df = df[df['matched'] == 1]
        
        result = [(str(row['case_id']).strip(), str(row['doc_name']).strip()) 
                  for _, row in df.iterrows()]
    else:
        # Get from top{k}_docs.csv using pandas
        csv_path = os.path.join(folder, f"top{top_k}_docs.csv")
        result = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0: 
                    continue
            
                line = line.strip()
                if not line:
                    continue
            
                # Split only on first comma: case_id, doc_names
                parts = line.split(',', 1)
                if len(parts) == 2:
                    case_id = parts[0].strip()
                    doc_names_str = parts[1].strip().strip('"')
                    doc_names = doc_names_str.split("|")
                    result.append((case_id, doc_names))
    
    
    # Save to CSV
    if save_csv:
        if save_dir is None:
            save_dir = folder
        save_path = os.path.join(save_dir, f"top{int(top_k)}_matched_docs.csv")
        _save_results_to_csv(result, top_k, save_path)
    
    print(f"Matched cases: {len(result)}")
    return result

def load_unmatched_cases(base_dir, rerank_model, top_k, save_csv=True, save_dir=None):
    """
    Load unmatched cases (matched=0) with top-k documents
    
    Args:
        base_dir: Base directory containing retrieval results
        rerank_model: Reranking model name
        top_k: Number of top documents to retrieve
        save_csv: Whether to save results as CSV
        save_dir: Directory to save CSV (default: same as data folder)
    
    Returns:
        top_k=1: [(case_id, doc_name), ...]
        top_k>1: [(case_id, [doc1, doc2, ...]), ...]
    """
    folder = _get_folder_path(base_dir, rerank_model, top_k)
    
    # Find matched=0 cases from matching_summary.csv using pandas
    df_summary = pd.read_csv(os.path.join(folder, "matching_summary.csv"))
    unmatched_ids = set(df_summary[df_summary['matched'] == 0]['case_id'].astype(str).str.strip())
    
    # Get top-k documents from rerank_orders.csv using manual parsing
    case_docs = {}
    with open(os.path.join(folder, "rerank_orders.csv"), "r", encoding="utf-8") as f:
        header = f.readline()
        num_cols = len(header.strip().split(','))

        for line in f:
            line = line.strip()
            if not line:
                continue
        
            parts = line.split(',')
            case_id = parts[0].strip()
            try:
                rank = int(parts[1].strip())
            except ValueError:
                continue

            if num_cols == 5:
                doc_name = ','.join(parts[2:-2]).strip()
            elif num_cols == 4:
                doc_name = ','.join(parts[2:-1]).strip()
            else:
                continue
            
            if case_id in unmatched_ids and rank <= top_k:
                if case_id not in case_docs:
                    case_docs[case_id] = []
                case_docs[case_id].append(doc_name)

    # Build result list
    result = []
    for case_id in sorted(case_docs.keys()):
        docs = case_docs[case_id]
        if top_k == 1:
            result.append((case_id, docs[0]))
        else:
            result.append((case_id, docs))
    
    # Save to CSV
    if save_csv:
        if save_dir is None:
            save_dir = folder
        save_path = os.path.join(save_dir, f"top{int(top_k)}_unmatched_docs.csv")
        _save_results_to_csv(result, top_k, save_path)
    
    print(f"Unmatched cases: {len(result)}")
    return result

def load_correct_cases(base_dir, rerank_model, top_k, save_csv=True, save_dir=None):
    """
    Load correct cases 
    
    Args:
        base_dir: Base directory containing retrieval results
        rerank_model: Reranking model name
        top_k: Number of top documents to retrieve
        save_csv: Whether to save results as CSV
        save_dir: Directory to save CSV (default: same as data folder)
    """
    folder = _get_folder_path(base_dir, rerank_model, top_k)

    csv_path = os.path.join(folder, "matching_summary.csv")
    df = pd.read_csv(csv_path)

    result = [(str(row['case_id']).strip(), str(row['doc_name']).strip()) 
                for _, row in df.iterrows()]
    
    # Save to CSV
    if save_csv:
        if save_dir is None:
            save_dir = folder
        save_path = os.path.join(save_dir, f"correct_cases.csv")
        df = pd.DataFrame(result, columns=['case_id', 'doc_names'])
        df.to_csv(save_path, index=False, encoding='utf-8', quoting=1)
    
    return result

def load_incorrect_cases(base_dir, rerank_model, top_k, save_csv=True, save_dir=None):
    """
    Load incorrect cases
    
    Args:
        base_dir: Base directory containing retrieval results
        rerank_model: Reranking model name
        top_k: Number of top documents to retrieve
        save_csv: Whether to save results as CSV
        save_dir: Directory to save CSV (default: same as data folder)
    """
    folder = _get_folder_path(base_dir, rerank_model, top_k)

    csv_path = os.path.join(folder, "matching_summary.csv")
    df = pd.read_csv(csv_path)

    case_ranks = {}

    with open(os.path.join(folder, "rerank_orders.csv"), "r", encoding="utf-8") as f:
        header = f.readline()
        num_cols = len(header.strip().split(','))
        
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(',')
            case_id = parts[0].strip()
            try:
                rank = int(parts[1].strip())
            except ValueError:
                continue
            
            # Extract doc_name based on column count
            if num_cols == 5:
                doc_name = ','.join(parts[2:-2]).strip()
            elif num_cols == 4:
                doc_name = ','.join(parts[2:-1]).strip()
            else:
                continue
            
            if case_id not in case_ranks:
                case_ranks[case_id] = []
            case_ranks[case_id].append((rank, doc_name))
    
    result = []
    for _, row in df.iterrows():
        case_id = str(row['case_id']).strip()
        matched = row['matched']

        ranks = sorted(case_ranks[case_id], key=lambda x: x[0])
        if matched == 1:
            llm_rank = row['llm_rank']
            incorrect_doc = None
            for rank, doc_name in ranks:
                if rank != llm_rank:
                    incorrect_doc = doc_name
                    break
            
            if incorrect_doc:
                result.append((case_id, incorrect_doc))
        else:
            if ranks:
                result.append((case_id, ranks[0][1]))

    # Save to CSV
    if save_csv:
        if save_dir is None:
            save_dir = folder
        save_path = os.path.join(save_dir, f"incorrect_cases.csv")
        result_df = pd.DataFrame(result, columns=['case_id', 'doc_names'])
        result_df.to_csv(save_path, index=False, encoding='utf-8', quoting=1)
    
    return result
    

if __name__ == "__main__":
    my_save_folder = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/toy_openai"
    exp_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/top1_10retrieve_gpt_5_mini_policy_openai_small"
    exp_dir2 = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/top3_30retrieve_gpt_5_mini_header_openai_small"
    
    load_correct_cases(
        base_dir=exp_dir2,
        rerank_model="gpt-5-mini",
        top_k=3,
        save_csv=True,
        save_dir=my_save_folder  
    )

    load_incorrect_cases(
        base_dir=exp_dir2,
        rerank_model="gpt-5-mini",
        top_k=3,
        save_csv=True,
        save_dir=my_save_folder  
    )

    # unmatched = load_unmatched_cases(
    #     base_dir=exp_dir2,
    #     rerank_model="gpt-5-mini",
    #     top_k=3,
    #     save_csv=True,
    #     save_dir=my_save_folder  
    # )

    # matched = load_matched_cases(
    #     base_dir=exp_dir2,
    #     rerank_model="gpt-5-mini",
    #     top_k=3,
    #     save_csv=True,
    #     save_dir=my_save_folder  
    # )