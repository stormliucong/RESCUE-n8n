import re
import os
import pandas as pd
from openai import OpenAI
from datetime import datetime


def normalize_provider_name(name):
    """normalize provider name according to specified rules"""
    name = name.strip()
    
    name = re.sub(r'[–—]', '-', name)
    name = re.sub(r'\s+', ' ', name)
    
    if name.lower().strip() == "oscar":
        name = "Oscar Health Insurance"
    
    # 3. Fix garbled characters
    name = re.sub(r"\?\?\s*Medicaid", "- Medicaid", name, flags=re.IGNORECASE)
    
    # 4. Kansas City → Kansas
    name = name.replace("Kansas City", "Kansas")
    
    # 5. Wellpoint (Amerigroup ...) → Wellpoint
    if re.search(r"Wellpoint\s*\(Amerigroup.*?\)", name, flags=re.IGNORECASE):
        name = "Wellpoint"
    
    # 6. Wellpoint (XX) → Wellpoint XX
    match = re.match(r"Wellpoint\s*\((\w{2})\)", name)
    if match:
        name = f"Wellpoint {match.group(1)}"
    
    # 7. State abbreviation mapping
    state_abbrev = {
        "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
        "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
        "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
        "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
        "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
        "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
        "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
        "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
        "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
        "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
    }
    
    # 8. Preserve full state name for certain providers
    preserve_state_full = [
        "Amerigroup", "Anthem BCBS", "BCBS", "Blue Cross", "CareSource", "Healthy Blue", "Molina Healthcare"
    ]
    
    should_preserve = False
    for prefix in preserve_state_full:
        if re.search(rf"^{prefix}\s+of\s+[A-Za-z ]+", name, flags=re.IGNORECASE):
            should_preserve = True
            break
    
    if not should_preserve:
        # 9. AmeriHealth Caritas State → AmeriHealth Caritas XX
        for state, abbr in state_abbrev.items():
            if re.fullmatch(rf"AmeriHealth Caritas {state}", name, flags=re.IGNORECASE):
                name = f"AmeriHealth Caritas {abbr}"
                break
            if re.fullmatch(rf"Wellpoint {state}", name, flags=re.IGNORECASE):
                name = f"Wellpoint {abbr}"
                break
        
        for state, abbr in state_abbrev.items():
            # BCBS California → BCBS CA
            if re.fullmatch(rf"BCBS {state}", name, flags=re.IGNORECASE):
                name = f"BCBS {abbr}"
                break
            # BCBS (CA) → BCBS CA  
            if re.fullmatch(rf"BCBS \({abbr}\)", name, flags=re.IGNORECASE):
                name = f"BCBS {abbr}"
                break
        
        # 11. X of State → X
        name = re.sub(r"\bof\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", "", name)
    
    # 12. Clean-up
    name = name.replace("&", "and")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\s*\(.*?\)", "", name)
    
    return name.strip()

def _save_llm_log(log_dir, log_data, model_name="gpt-4o"):
    """Save LLM evaluation log entry to CSV."""
    log_path = os.path.join(log_dir, f"llm_evaluation_log_{model_name}.csv")
    log_entry = pd.DataFrame([log_data])
    
    if os.path.exists(log_path):
        log_entry.to_csv(log_path, mode='a', header=False, index=False, encoding='utf-8')
    else:
        log_entry.to_csv(log_path, mode='w', header=True, index=False, encoding='utf-8')

def _parse_llm_response(response_text):
    """Parse LLM response."""
    common_match = re.search(r'\*{0,2}Common Count\*{0,2}:\s*(\d+)', response_text, re.IGNORECASE)
    common_count = int(common_match.group(1)) if common_match else 0
    
    common_providers_match = re.search(r'\*{0,2}Common Providers\*{0,2}:\s*\[(.*?)\]', response_text, re.DOTALL | re.IGNORECASE)
    if common_providers_match:
        common_text = common_providers_match.group(1).strip()
        common_providers = [item.strip().strip('"\'') for item in common_text.split(',') 
                          if item.strip() and item.strip() != 'None']
    else:
        common_providers = []
    
    missing_match = re.search(r'\*{0,2}Missing Providers\*{0,2}:\s*\[(.*?)\]', response_text, re.DOTALL | re.IGNORECASE)
    if missing_match:
        missing_text = missing_match.group(1).strip()
        missing = [item.strip().strip('"\'') for item in missing_text.split(',') 
                  if item.strip() and item.strip() != 'None']
    else:
        missing = []
    
    extra_match = re.search(r'\*{0,2}Extra Providers\*{0,2}:\s*\[(.*?)\]', response_text, re.DOTALL | re.IGNORECASE)
    if extra_match:
        extra_text = extra_match.group(1).strip()
        extra = [item.strip().strip('"\'') for item in extra_text.split(',') 
                if item.strip() and item.strip() != 'None']
    else:
        extra = []
    
    return common_count, common_providers, missing, extra    

def llm_evaluate(predicted, ground_truth, openai_client, log_dir, model_name="gpt-4o"):
    """Evaluate using LLM comparison."""
    
    os.makedirs(log_dir, exist_ok=True)
    
    if not predicted or not ground_truth:
        result = {
            "ground_truth_count": len(ground_truth),
            "llm_returned_count": len(predicted),
            "common_count": 0,
            "missing_count": len(ground_truth),
            "extra_count": len(predicted),
            "common_providers": [],
            "missing_providers": list(ground_truth),
            "extra_providers": list(predicted),
            "precision": 0.0,
            "recall": 0.0
        }
        
        _save_llm_log(log_dir, {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ground_truth_count': len(ground_truth),
            'predicted_count': len(predicted),
            'llm_raw_response': 'EMPTY_LISTS',
            'common_count': 0,
            'common_providers': '',
            'missing_providers': '',
            'extra_providers': '',
            'precision': 0.0,
            'recall': 0.0,
            'error': ''
        }, model_name)
        return result
    
    prompt = f"""
You are an expert evaluator tasked with comparing two healthcare provider lists to calculate precision and recall metrics.

Your job is to:
1. Compare the Predicted list (experimental results) against the Ground Truth list
2. Identify which providers represent the same healthcare insurance entity
3. Calculate standard evaluation metrics

Matching Rules:
- Medicaid suffix is a KEY DIFFERENTIATOR: "Dean Health Plan" ≠ "Dean Health Plan – Medicaid" (different entities)
- Special characters/spacing/capitalization differences are IGNORED: "AmeriHealth" = "Amerihealth", "Anthem – Medicaid" = "Anthem - Medicaid"
- Company name extensions are considered same entity: "Oscar" = "Oscar Health Insurance"
- United Healthcare plans are ALL DIFFERENT entities: "United Healthcare" ≠ "United Healthcare Community Plan" ≠ "United Healthcare Community Plan (DC)"
- BCBS regional plans are different entities: "BCBS Texas" ≠ "BCBS Minnesota"

Examples:
- MATCH: "BCBS California" ↔ "BCBS CA" ↔ "BCBS (CA)" (same region, different abbreviations)
- MATCH: "Oscar" ↔ "Oscar Health Insurance"
- MATCH: "Anthem – Medicaid" ↔ "Anthem - Medicaid" (dash vs em-dash)
- NO MATCH: "Dean Health Plan" ↔ "Dean Health Plan – Medicaid" (different entities)
- NO MATCH: "BCBS Texas" ↔ "BCBS Minnesota" (different regions)

Step-by-step process:
1. First, identify all exact matches between the two lists following the rules above
2. Count matched providers (common_count)
3. List unmatched Ground Truth providers (missing)
4. List unmatched Predicted providers (extra)

Ground Truth ({len(ground_truth)} providers):
{chr(10).join([f"{i+1}. {gt}" for i, gt in enumerate(ground_truth)])}

Predicted ({len(predicted)} providers):
{chr(10).join([f"{i+1}. {pred}" for i, pred in enumerate(predicted)])}

Please provide your analysis and results in the following format:
Common Count: [number]
Common Providers: [list]
Missing Providers: [list]
Extra Providers: [list]
"""
    
    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.choices[0].message.content
        common_count, common_providers, missing, extra = _parse_llm_response(response_text)  # helper 사용
        
        precision = (common_count / len(predicted) * 100) if predicted else 0
        recall = (common_count / len(ground_truth) * 100) if ground_truth else 0
        
        result = {
            "ground_truth_count": len(ground_truth),
            "llm_returned_count": len(predicted),
            "common_count": common_count,
            "missing_count": len(missing),
            "extra_count": len(extra),
            "common_providers": sorted(common_providers),
            "missing_providers": sorted(missing),
            "extra_providers": sorted(extra),
            "precision": round(precision, 2),
            "recall": round(recall, 2)
        }
        
        _save_llm_log(log_dir, { 
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ground_truth_count': len(ground_truth),
            'predicted_count': len(predicted),
            'llm_raw_response': response_text.replace('\n', '\\n'),
            'common_count': common_count,
            'common_providers': '|'.join(common_providers),
            'missing_providers': '|'.join(missing),
            'extra_providers': '|'.join(extra),
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'error': ''
        }, model_name)
        return result
        
    except Exception as e:
        print(f"LLM evaluation error: {e}")
        
        _save_llm_log(log_dir, { 
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ground_truth_count': len(ground_truth),
            'predicted_count': len(predicted),
            'llm_raw_response': f'ERROR: {str(e)}',
            'common_count': 0,
            'common_providers': '',
            'missing_providers': '',
            'extra_providers': '',
            'precision': 0.0,
            'recall': 0.0,
            'error': str(e)
        }, model_name)

        return {
            "ground_truth_count": len(ground_truth),
            "llm_returned_count": len(predicted),
            "common_count": 0,
            "missing_count": len(ground_truth),
            "extra_count": len(predicted),
            "common_providers": [],
            "missing_providers": list(ground_truth),
            "extra_providers": list(predicted),
            "precision": 0.0,
            "recall": 0.0
        }
    
def exact_match(predicted, ground_truth):
    """ Exact Match (no normalization) """
    pred_set = set(predicted)
    gt_set = set(ground_truth)
    common = len(pred_set & gt_set)
    
    precision = (common / len(pred_set) * 100) if pred_set else 0
    recall = (common / len(gt_set) * 100) if gt_set else 0
    
    return precision, recall

def regex_match(predicted, ground_truth):
    """ Regex Match """
    pred_set = set(normalize_provider_name(p) for p in predicted)
    gt_set = set(normalize_provider_name(g) for g in ground_truth)
    common = len(pred_set & gt_set)
    
    precision = (common / len(pred_set) * 100) if pred_set else 0
    recall = (common / len(gt_set) * 100) if gt_set else 0
    
    return precision, recall