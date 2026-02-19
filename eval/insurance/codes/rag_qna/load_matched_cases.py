import os
import pandas as pd

def load_matched_cases(base_dir, rerank_model, top_k, save_csv=True):
    """
    Load matched cases (matched=1) with top-k documents
    
    top_k=1: [(case_id, doc_name), ...]
    top_k>1: [(case_id, [doc1, doc2, ...]), ...]
    """
    if top_k == 1:
        csv_path = os.path.join(base_dir, "retrieval", rerank_model.replace("-", "_"), 
                               f"top{int(top_k)}", "matching_summary.csv")
        df = pd.read_csv(csv_path)
        df = df[df['matched'] == 1]  # Filter matched=1
        
        result = []
        for _, row in df.iterrows():
            case_id = str(row['case_id']).strip()
            doc_name = str(row['doc_name']).strip()
            result.append((case_id, doc_name))
            print(f" Case {len(result)}: {case_id} -> {doc_name}")
    else:
        csv_path = os.path.join(base_dir, "retrieval", rerank_model.replace("-", "_"), 
                               f"top{int(top_k)}", f"top{top_k}_docs.csv")
        result = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0:  # Skip header
                    continue
                line = line.strip()
                if line:
                    parts = line.split(',', 1)  # Only split on first comma
                    if len(parts) == 2:
                        case_id = parts[0].strip()
                        doc_names_str = parts[1].strip().strip('"')
                        doc_names = doc_names_str.split("|")
                        result.append((case_id, doc_names))
                        print(f" Case {len(result)}: {case_id} -> {len(doc_names)} docs: {doc_names}")
    # Save as CSV using pandas
    if save_csv:
        save_path = os.path.join(base_dir, "retrieval", rerank_model.replace("-", "_"), 
                                f"top{int(top_k)}", f"top{int(top_k)}_matched_docs.csv")
        
        if top_k == 1:
            df_save = pd.DataFrame(result, columns=['case_id', 'doc_names'])
        else:
            df_data = [(case_id, "|".join(docs)) for case_id, docs in result]
            df_save = pd.DataFrame(df_data, columns=['case_id', 'doc_names'])
        
        df_save.to_csv(save_path, index=False, encoding='utf-8', quoting=1)
        print(f"Saved to: {save_path}")
    
    print(f"Matched cases: {len(result)}")
    return result

if __name__ == "__main__":
    # import tempfile
    # base_dir = tempfile.mkdtemp(prefix="load_matched_cases_")
    # model = "gpt-5-mini"
    # model_dir = model.replace("-", "_")
    # top1_dir = os.path.join(base_dir, "retrieval", model_dir, "top1")
    # top3_dir = os.path.join(base_dir, "retrieval", model_dir, "top3")

    # os.makedirs(top1_dir, exist_ok=True)
    # os.makedirs(top3_dir, exist_ok=True)

    # top1_csv = os.path.join(top1_dir, "matching_summary.csv")
    # pd.DataFrame(
    # [
    #     ["Case1", 1, 1, 3, "A,C.pdf"],
    #     ["Case2", 1, 1, 1, "B.pdf"],
    #     ["Case3", 0, 4, 2, ""] 
    # ],
    #     columns=["case_id", "matched", "llm_rank", "orig_rank", "doc_name"] # match result first (rerank top-3) 1, (1,2,3), 3 
    # ).to_csv(top1_csv, index=False)
    
    # top3_csv = os.path.join(top3_dir, "top3_docs.csv")
    # pd.DataFrame(
    # [
    #     ["Case1", "A.pdf|C,J,K.pdf|D.pdf"],
    #     ["Case2", "B.pdf|E.pdf|F.pdf"],
    #     ["Case3", "G.pdf|H.pdf|I.pdf"]
    # ],
    #     columns=["case_id", "doc_names"]
    # ).to_csv(top3_csv, index=False)

    # res1 = load_matched_cases(base_dir, rerank_model=model, top_k=1)
    # assert len(res1) == 2
    # assert res1[0] == ("Case1", "A,C.pdf")
    # assert res1[1] == ("Case2", "B.pdf")

    # res3 = load_matched_cases(base_dir, rerank_model=model, top_k=3)
    # assert len(res3) == 3
    # assert res3[0] == ("Case1", ["A.pdf", "C,J,K.pdf", "D.pdf"])
    # assert res3[1] == ("Case2", ["B.pdf", "E.pdf", "F.pdf"])

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
                        matched = load_matched_cases(
                            base_dir=save_base_dir,
                            rerank_model=RETRIEVAL_MODEL,
                            top_k=K_RERANK,
                            save_csv=True
                        )
                        print(f"  ✅ {len(matched)} matched cases")

                    except Exception as e:
                        print(f"  ❌ Error: {str(e)}")