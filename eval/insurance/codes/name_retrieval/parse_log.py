import re

def _parse_llm_response(response_text):
    """Parse all observed LLM response formats"""
    
    # Unescape newlines from CSV
    if '\\n' in response_text:
        response_text = response_text.replace('\\n', '\n')
    
    # Common Count
    common_match = re.search(r'Common Count:\s*(\d+)', response_text, re.IGNORECASE)
    common_count = int(common_match.group(1)) if common_match else 0
    
    def extract_list(section_name, text):
        """Extract provider list - supports all 3 observed formats"""
        
        pattern = (
            rf'(?:#{{{1,4}}}\s*)?'  # Optional markdown header
            rf'(?:\*\*)?'            # Optional opening **
            rf'{section_name}'       # Section name
            rf'(?:\*\*)?'            # Optional closing **
            rf'(?:\s*\([^)]*\))?'    # Optional (description)
            rf':\s*\n'               # Colon and newline
            rf'((?:[-\d]+\.?\s+.+(?:\n|$))+)'  # List items (numbered or bullet)
        )
        
        match = re.search(pattern, text, re.IGNORECASE)
        
        if not match:
            return []
        
        lines = match.group(1).strip().split('\n')
        items = []
        for line in lines:
            # Remove prefixes: "1. ", "2. ", "- ", etc.
            clean = re.sub(r'^[-\d]+\.?\s+', '', line).strip()
            if clean and not clean.startswith(('Common Count', 'Missing', 'Extra')):
                items.append(clean)
        
        return items
    
    common_providers = extract_list('Common Providers', response_text)
    missing_providers = extract_list('Missing Providers', response_text)
    extra_providers = extract_list('Extra Providers', response_text)
    
    return common_count, common_providers, missing_providers, extra_providers

if __name__ == "__main__":
    import pandas as pd

    log_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/name_retrieval/evaluation_results/llm_evaluation_log_gpt-4o.csv"
    df = pd.read_csv(log_path)
    
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    latest_date = df['date'].max()
    latest_data = df[df['date'] == latest_date]
    
    print(f"=== Testing with date: {latest_date} ===")
    sample = latest_data['llm_raw_response'].iloc[-1]
    
    count, common, missing, extra = _parse_llm_response(sample)
    print(f"Common Count: {count}")
    print(f"Parsed Common: {len(common)} items")
    print(f"Parsed Missing: {len(missing)} items")
    print(f"Parsed Extra: {len(extra)} items")
    
    if len(common) > 0:
        print(f"\nFirst 5 common: {common[:5]}")