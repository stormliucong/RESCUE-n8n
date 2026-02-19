import os
import json
import pandas as pd
from pathlib import Path

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def extract_metadata_from_path(filepath):
    """
    Extract experiment metadata from file path
    Works for both RAG/Baseline and File_Agent paths
    """
    parts = Path(filepath).parts
    
    # Defaults
    metadata = {
        "embedding_type": "N/A",
        "mode": "N/A", 
        "case_type": "N/A",
        "exp_type": "N/A",
        "k_retrieval": None,
        "k_rerank": None,
        "retrieval_model": "N/A",
        "qna_model": "N/A"
    }
    
    # Check each part of path
    for part in parts:
        # Embedding type
        if part == "ST":
            metadata["embedding_type"] = "sentence_transformer"
        elif part == "open_ai":
            metadata["embedding_type"] = "openai"
        elif part == "File_Agent":
            metadata["embedding_type"] = "file_agent"
            metadata["mode"] = "file_agent"
        
        # Mode
        if part in ["rag", "baseline"]:
            metadata["mode"] = part
        
        # Case type
        if part in ["matched", "unmatched", "all_correct", "all_incorrect"]:
            metadata["case_type"] = part
        
        # Experiment config (e.g., header_k10_rerank1)
        if "_k" in part and "_rerank" in part:
            pieces = part.split('_')
            metadata["exp_type"] = pieces[0]  # header or policy
            for i, piece in enumerate(pieces):
                if piece.startswith('k'):
                    metadata["k_retrieval"] = int(pieces[i].replace('k', ''))
                if piece.startswith('rerank'):
                    metadata["k_rerank"] = int(piece.replace('rerank', ''))
        
        if part.startswith("iter") and len(part) > 4 and part[4:].isdigit():
            metadata["iteration"] = part
        
        # Model names (e.g., gpt-5-mini, gpt-4o)
        if part.startswith("gpt"):
            metadata["qna_model"] = part
            if "gpt_" in part:  # RAG format: gpt_5_mini_gpt_5_mini
                models = part.split('_gpt_')
                metadata["retrieval_model"] = f"gpt_{models[0].split('_', 1)[1]}"
                metadata["qna_model"] = f"gpt_{models[1]}"
    
    return metadata

def flatten_qna_results(json_data, is_file_agent=False):
    """
    Flatten Q0-Q8 answers and token info into a flat dict
    """
    result = {}
    
    if is_file_agent:
        # File_Agent: {"Q0": "WES", "Q1": "Yes", ...}
        for i in range(9):
            q_data = json_data.get(f"Q{i}", {})
            result[f"Q{i}_answer"] = q_data.get("answer")
            result[f"Q{i}_reasoning"] = q_data.get("reasoning")
        result["md5_hash"] = json_data.get("md5_hash")
    else:
        # RAG/Baseline: {"qna_result": {"Q0": {"answer": ..., "reasoning": ...}}}
        qna = json_data.get("qna_result", {})
        for i in range(9):
            q_data = qna.get(f"Q{i}", {})
            result[f"Q{i}_answer"] = q_data.get("answer")
            result[f"Q{i}_reasoning"] = q_data.get("reasoning")
        result["md5_hash"] = None
    
    # Token usage
    tokens = json_data.get("token_usage", {})
    result["input_tokens"] = tokens.get("input_tokens")
    result["output_tokens"] = tokens.get("output_tokens")
    result["total_tokens"] = tokens.get("total_tokens")
    
    return result

def process_all_json_files(base_path):
    """
    Find and process all JSON result files
    """
    all_rows = []
    
    # Find all JSON files recursively
    for json_file in Path(base_path).rglob("*.json"):
        # Skip batch/log files
        if any(x in str(json_file) for x in ["batch", "ground_truth", "Insurance_Genetic"]):
            continue
        
        # Load JSON
        data = load_json_file(json_file)
        if not data:
            continue
        
        # Extract metadata from path
        metadata = extract_metadata_from_path(str(json_file))
        
        # Determine if File_Agent
        is_file_agent = metadata["embedding_type"] == "file_agent"
        
        # Get case_id from filename
        case_id = json_file.stem.split('_')[0]
        
        # Flatten QnA results
        qna_data = flatten_qna_results(data, is_file_agent)
        
        # Combine everything
        row = {"case_id": case_id, **metadata, **qna_data}
        all_rows.append(row)
    
    return all_rows

def save_experiment_csvs(df, base_path):
    """Save CSV for each experiment folder"""
    
    # Process RAG data
    rag_df = df[df['mode'] == 'rag']
    if not rag_df.empty:
        for (iteration, case_type), group in rag_df.groupby(['iteration', 'case_type']):
            if pd.isna(iteration):  # Skip if no iteration
                continue
            save_dir = os.path.join(base_path, "open_ai", "gpt_5_mini_gpt_5_mini", "rag", iteration, case_type)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, "results.csv")
            group.to_csv(save_path, index=False)
            print(f"Saved {save_path}: {len(group)} rows")
    
    # Process Baseline data
    baseline_df = df[df['mode'] == 'baseline']
    if not baseline_df.empty:
        for iteration, group in baseline_df.groupby('iteration'):
            if pd.isna(iteration):  # Skip if no iteration
                continue
            save_dir = os.path.join(base_path, "open_ai", "gpt_5_mini_gpt_5_mini", "baseline", iteration)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, "results.csv")
            group.to_csv(save_path, index=False)
            print(f"Saved {save_path}: {len(group)} rows")

def aggregate_all_results(base_path="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/RAG/final/final_qna_results"):
    """
    Main function: aggregate all results into CSVs
    """
    print("Scanning for JSON files...")
    
    # Process all JSON files
    all_rows = process_all_json_files(base_path)
    print(f"Found {len(all_rows)} result files")
    
    # Create DataFrame
    df = pd.DataFrame(all_rows)
    
    df.loc[df['mode'] == 'baseline', 'case_type'] = 'without_policy'

    # Organize columns
    base_cols = ["case_id", "mode", "case_type", "iteration"]
    qna_cols = [f"Q{i}_{field}" for i in range(9) for field in ["answer", "reasoning"]]
    token_cols = ["input_tokens", "output_tokens", "total_tokens"]
    df = df[base_cols + qna_cols + token_cols]
    
    # Save experiment CSVs
    print("\nSaving experiment CSVs...")
    save_experiment_csvs(df, base_path)
    
    # Save combined CSV
    combined_path = os.path.join(base_path, "final_all_results_combined.csv")
    df.to_csv(combined_path, index=False)
    
    print(f"\nCombined CSV: {combined_path}")
    print(f"Total: {len(df)} rows, {len(df.columns)} columns")
    print("\nSummary by experiment:")
    print(df.groupby(['mode', 'case_type', 'iteration']).size())
    
    return df

if __name__ == "__main__":
    df = aggregate_all_results()
    print("\nAggregation complete.")