import os
import glob
import PyPDF2 
import hashlib

def calculate_pdf_md5(pdf_path):
    ''' Compute content MD5 of a PDF file'''
    with open(pdf_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest() # calculate the md5 hash of the pdf file

def load_policies(pdf_path):
    ''' Load all pdf policies and extract content / compute MD5 '''
    pdf_files = glob.glob(os.path.join(pdf_path, "*.pdf")) # find all the pdf files from the path
     
    policies = {}
    md5s = {}
    headers = {} 

    for pdf_file in pdf_files:
        fname = os.path.basename(pdf_file)

        with open(pdf_file, "rb") as f: # open the pdf file in binary mode
            reader = PyPDF2.PdfReader(f) 
            pages = [page.extract_text() or "" for page in reader.pages] # extract text from each page

        full_text = "\n\n".join(pages)
        policies[fname] = full_text
        md5s[fname] = calculate_pdf_md5(pdf_file)

        headers_lines = []
        KEYS = ["coverage", "guidelines", "criteria", "medical necessity"]

        for p in pages[:5]:
             for line in p.split("\n"):
                ll = line.strip()
                low = ll.lower()
                if any(k in low for k in KEYS):
                    headers_lines.append(ll)    
        headers[fname] = " ".join(headers_lines) or full_text[:2000]
    
    print(f"Loaded {len(policies)} policies.")
    return policies, md5s, headers

if __name__ == "__main__":
    folder = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_answer_real"
    policies, md5s, headers = load_policies(folder)
    assert isinstance(policies, dict) and isinstance(md5s, dict) and isinstance(headers, dict)
    assert len(policies) == len(md5s) == len(headers)
    assert headers.keys() == policies.keys() == md5s.keys()
