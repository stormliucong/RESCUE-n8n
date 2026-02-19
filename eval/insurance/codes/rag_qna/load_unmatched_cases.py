import os
import pandas as pd

def load_unmatched_cases(base_dir, rerank_model, top_k, save_csv=True):
    """
    Load unmatched cases (matched=0) with top-k documents
    
    top_k=1: [(case_id, doc_name), ...]
    top_k>1: [(case_id, [doc1, doc2, ...]), ...]
    """
    folder = os.path.join(base_dir, "retrieval", rerank_model.replace("-", "_"), f"top{int(top_k)}")
    
    # Find unmatched cases (matched=0)
    unmatched_ids = set()
    with open(os.path.join(folder, "matching_summary.csv"), "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0: 
                continue
            parts = line.strip().split(',', 5)
            if len(parts) >= 2:
                case_id = parts[0].strip()
                matched = parts[1].strip()
                if matched == '0':
                    unmatched_ids.add(case_id)
    
    # Collect top-k documents from rerank_orders.csv
    case_docs = {}
    
    with open(os.path.join(folder, "rerank_orders.csv"), "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == 0:  
                continue
            parts = line.strip().split(',')
            if len(parts) >= 3:
                case_id = parts[0].strip()
                rank = int(parts[1].strip())
                doc_name = parts[2].strip()
                
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
            print(f" Case {len(result)}: {case_id} -> {docs[0]}")
        else:
            result.append((case_id, docs))
            print(f" Case {len(result)}: {case_id} -> {len(docs)} docs: {docs}")
    
    # Save as CSV using pandas
    if save_csv:
        csv_path = os.path.join(folder, f"top{int(top_k)}_unmatched_docs.csv")
        
        if top_k == 1:
            df = pd.DataFrame(result, columns=['case_id', 'doc_names'])
        else:
            # Join list with "|"
            df_data = [(case_id, "|".join(docs)) for case_id, docs in result]
            df = pd.DataFrame(df_data, columns=['case_id', 'doc_names'])
        
        df.to_csv(csv_path, index=False, encoding='utf-8', quoting=1)
        print(f"Saved to: {csv_path}")
    
    print(f"Unmatched cases: {len(result)}")
    return result

if __name__ == "__main__":
    BASE_RESULTS_DIR = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final"
    
    K_RETRIEVAL_LIST = [10, 30]
    K_RERANK_LIST = [1, 3]
    RETRIEVAL_MODELS = ["gpt-5-mini", "gpt-5"]
    QNA_MODELS = ["gpt-5-mini", "gpt-5"]

    for RETRIEVAL_MODEL in RETRIEVAL_MODELS:
        for QNA_MODEL in QNA_MODELS:
            for K_RETRIEVAL in K_RETRIEVAL_LIST:
                for K_RERANK in K_RERANK_LIST:
                    
                    exp_dir = (
                        f"top{K_RERANK}_{K_RETRIEVAL}retrieve_"
                        f"{RETRIEVAL_MODEL.replace('-','_')}_"
                        f"{QNA_MODEL.replace('-','_')}_update"
                    )
                    save_base_dir = os.path.join(BASE_RESULTS_DIR, exp_dir)

                    try:
                        unmatched = load_unmatched_cases(
                            base_dir=save_base_dir,
                            rerank_model=RETRIEVAL_MODEL,
                            top_k=K_RERANK,
                            save_csv=True
                        )
                        print(f"  ✅ {len(unmatched)} unmatched cases")
                        
                    except Exception as e:
                        print(f"  ❌ Error: {str(e)}")