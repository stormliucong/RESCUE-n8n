import json
from download_pdf import download_pdf, calculate_md5
import os
import pandas as pd

def count_links(file_path):
    output_csv = os.path.join(os.path.dirname(file_path), 'links_summary.csv')

    with open(file_path, 'r') as f:
        data = json.load(f)
    
    payer = data['payer']
    pdf_links = data['parsed_data']['pdf_links']
    webpage_links = data['parsed_data']['webpage_links']
    
    clean_pdf_links = []
    for link in pdf_links:
        if isinstance(link, dict):
            clean_pdf_links.append(link.get('link', ''))
        else:
            clean_pdf_links.append(link)
    
    clean_webpage_links = []
    for link in webpage_links:
        if isinstance(link, dict):
            clean_webpage_links.append(link.get('link', ''))
        else:
            clean_webpage_links.append(link)

    result = {
        'payer': payer,
        'pdf_count': len(clean_pdf_links),
        'webpage_count': len(clean_webpage_links),
        'pdf_links': clean_pdf_links,
        'webpage_links': clean_webpage_links,
        'total_links_count': len(clean_pdf_links) + len(clean_webpage_links)
    }
    
    result_df = pd.DataFrame([result])
    result_df.to_csv(output_csv, index=False)
    
    return result

def process_pdf(json_file_path, download_dir, output_csv):
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    payer = data['payer']
    pdf_links = data['parsed_data']['pdf_links']

    os.makedirs(download_dir, exist_ok=True)

    results = []
    for i, url in enumerate(pdf_links, 1):
        if isinstance(url, dict):
            url = url.get('link', '')
            if not url:
                continue

        filename = url.split('/')[-1]
        save_path = os.path.join(download_dir, filename)
        
        if download_pdf(url, save_path):
            md5 = calculate_md5(save_path)
            if md5:
                print(f"   MD5: {md5}\n")
                results.append({
                    'payer': payer,
                    'filename': filename,
                    'url': url,
                    'md5': md5
                })
        
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    
    return results


if __name__ == "__main__":
    import os
    results_dir = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/payer_retrieval/final/iteration_3/gpt-4o/verified/Cigna"
    result_file = os.path.join(results_dir, "Cigna_result.json")

    links_summary = count_links(result_file)
    print(links_summary)

    result_ex = process_pdf(result_file, os.path.join(results_dir, "downloaded"), os.path.join(results_dir, "downloaded_pdfs.csv"))