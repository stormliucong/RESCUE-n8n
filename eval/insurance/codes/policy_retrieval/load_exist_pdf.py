import os
import pandas as pd
from download_pdf import calculate_md5

def load_existing_records(manual_pdf_folder, known_links_csv):
    """Load existing records from payer-specific PDF folders and CSV link list"""
    records = {
        "known_pdfs": {},
        "known_webpages": {}
    }
    
    # Load existing PDF files by payer
    if manual_pdf_folder and os.path.exists(manual_pdf_folder):
        print(f"Loading known PDFs from: {manual_pdf_folder}")
        
        # Record pdf files by payer and their md5 hash
        for payer_folder in os.listdir(manual_pdf_folder):
            payer_path = os.path.join(manual_pdf_folder, payer_folder)
            
            if os.path.isdir(payer_path):
                payer_name = payer_folder.replace("_", " ")
                records["known_pdfs"][payer_name] = {}
                
                for root, _, files in os.walk(payer_path):
                    for file in files:
                        if file.endswith('.pdf'):
                            file_path = os.path.join(root, file)
                            md5 = calculate_md5(file_path)
                            if md5:
                                records["known_pdfs"][payer_name][md5] = file_path
                
                print(f"   Found {len(records['known_pdfs'][payer_name])} PDFs for {payer_name}")
    
    # Load known webpage links from CSV
    if known_links_csv and os.path.exists(known_links_csv):
        print(f"Loading known webpage links from: {known_links_csv}")
        try:
            df = pd.read_csv(known_links_csv)
            for _, row in df.iterrows():
                payer = row['Providers']  
                source = row['Source']  
                links_str = row['Links'] 
                
                # HTML link
                if source == 'html' and pd.notna(links_str) and str(links_str).strip():
                    links = [link.strip() for link in str(links_str).split('\n') if link.strip()]
                    records["known_webpages"][payer] = links
                else:
                    records["known_webpages"][payer] = []
        except Exception as e:
            print(f"Failed to load webpage links CSV: {e}")
    
    return records