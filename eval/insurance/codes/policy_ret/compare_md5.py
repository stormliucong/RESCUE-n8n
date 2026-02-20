import pandas as pd
import os
from download_pdf import calculate_md5

def compare_md5(downloaded_csv, existing_pdfs_base_dir, output_csv, payer_mapping):
    '''Compare MD5 hashes of downloaded PDFs with existing PDFs and summarize results'''
    
    df = pd.read_csv(downloaded_csv)
    
    summary = []
    
    for payer in df['payer'].unique():
        payer_df = df[df['payer'] == payer]
        actual_folder_name = payer_mapping.get(payer, payer)
        payer_folder = os.path.join(existing_pdfs_base_dir, actual_folder_name)
        
        existing_md5_set = set()
        existing_pdf_count = 0
        if os.path.exists(payer_folder):
            for filename in os.listdir(payer_folder):
                if filename.endswith('.pdf'):
                    existing_pdf_count += 1
                    file_path = os.path.join(payer_folder, filename)
                    md5 = calculate_md5(file_path)
                    if md5:
                        existing_md5_set.add(md5)
        
        downloaded_count = len(payer_df)
        match_count = sum(1 for md5 in payer_df['md5'] if md5 in existing_md5_set)
        
        summary.append({
            'payer': payer,
            'existing_pdf_count': existing_pdf_count,
            'downloaded_pdf_count': downloaded_count,
            'matched_count': match_count,
            'new_count': downloaded_count - match_count
        })
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_csv, index=False)
    return summary_df

if __name__ == "__main__":
    downloaded_csv = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/payer_retrieval/example/iteration_1/gpt-5-mini/verified/United_Healthcare/downloaded_pdfs.csv"
    existing_pdfs_base_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_ret"
    output_csv = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/payer_retrieval/example/iteration_1/gpt-5-mini/verified/United_Healthcare/md5_comparison_results.csv"

    compare_md5(downloaded_csv, existing_pdfs_base_dir, output_csv)