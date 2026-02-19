import os
import json
import requests
import re

def format_questions(questions_list, indent=2):
    """Format a list of question dicts into a single prompt chunk."""
    indent_str = " " * indent
    blocks = []
    for q in questions_list:
        block = f"{q['id']}. {q['question']}\n{indent_str}Options: {', '.join(q['options'])}"
        blocks.append(block)
    return "\n\n".join(blocks)

def clean_json_response(response_text):
    """Return a parsed JSON object from an LLM response, stripping code fences and extra text."""
    # Clean and extract JSON from the response text
    original = response_text.strip()

    # Step 0: Check for hallucinated greeting (Perplexity fallback)
    if "how can I assist you" in original.lower() or "insurance-related questions" in original.lower():
        raise ValueError("Perplexity returned generic assistant response instead of JSON.")

    # Step 1: Try direct parsing
    try:
        return json.loads(original)
    except json.JSONDecodeError:
        pass

    # Step 2: Remove code block wrappers
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", original, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 3: Try to extract the first {...} JSON-like block
    match = re.search(r"(\{[\s\S]*?\})", original)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError("No valid JSON found in the response.")

def build_baseline_cached_prefix(formatted_questions):
    """Return the full QnA input text (shared prefix first for prompt caching)."""
    return f"""
IMPORTANT INTERPRETATION RULE: When no explicit insurance policy document is provided, any reference to “insurance policy”, “policy” or “eligibility criteria” should be interpreted using payer-specific coverage criteria as applied to the patient’s clinical presentations. The patient’s insurance payer is specified in the patient information. This is not a general coverage knowledge task. You should reason as if recalling the payer’s actual medical policy rules from your internal knowledge.
You will be given patient clinical information only.
Instructions: 
- Use the provided patient information as the sole source of patient-specific facts.
- Provide brief reasoning for each answer, and explicitly state the basis of your decision.
- Apply your internal knowledge of the specified payer’s published medical policy criteria relevant to the patient’s clinical context when answering and reasoning.
- Frame all reasoning from an insurance coverage adjudication perspective based on the payer-specific insurance coverage criteria.
- Output answers in JSON format ONLY. 

Focus on the following criteria when answering:

- **Age criteria**
- **Medical necessity criteria**
- **Prior test criteria**
- **Family history information** 
- **Related CPT codes**
- **Coverage criteria**
- **Counseling / Provider criteria**

Questions to answer:
{formatted_questions}

Answer options for each question (use these exact strings):
- Q0: ["WES", "WGS", "BRCA1/2", "CMA", "Question Unclear", "Not Answerable"]
- Q1: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q2: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q3: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q4: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q5: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q6: ["Yes", "No", "Not Specified", "Question Unclear", "Not Answerable"]
- Q7: ["81162", "81277", "81228", "81415", "81425", "Not Specified", "Question Unclear", "Not Answerable"]
- Q8: ["Yes", "No"]

Output format - Your response must follow this exact JSON structure:
{{
  "Q0": {{
    "answer": "<select from Q0 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q1": {{
    "answer": "<select from Q1 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q2": {{
    "answer": "<select from Q2 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q3": {{
    "answer": "<select from Q3 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q4": {{
    "answer": "<select from Q4 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q5": {{
    "answer": "<select from Q5 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q6": {{
    "answer": "<select from Q6 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q7": {{
    "answer": "<select from Q7 options>",
    "reasoning": "<brief explanation>"
  }},
  "Q8": {{
    "answer": "<select from Q8 options>",
    "reasoning": "<brief explanation>"
  }}
}}
"""

def build_baseline_qna_input_cached(patient_info, cached_prefix):
    """Build the variable part and combine with cached prefix."""
    return cached_prefix + f"""Patient Information:
{patient_info}"""

def run_baseline_qna(
    patient_info,
    case_id,
    qna_model,
    cached_prefix,
    save_dir,
    openai_client=None,
    clean_json_response_fn=None
):
    '''Run QnA over a matched policy (full text) and patient info.'''


    prompt = build_baseline_qna_input_cached(
        patient_info=patient_info,
        cached_prefix=cached_prefix
    )

    messages = [
        {"role": "system", "content": "You are a clinical insurance assistant specializing in genetic testing coverage policies."},
        {"role": "user",   "content": prompt}
    ]

    params = {"model": qna_model, "messages": messages}
    if "gpt-5" not in qna_model.lower():
        params["temperature"] = 0

    resp = openai_client.chat.completions.create(**params)
    result_content = resp.choices[0].message.content.strip()
    input_tokens = resp.usage.prompt_tokens if resp.usage else 0
    output_tokens = resp.usage.completion_tokens if resp.usage else 0

    # Parse JSON response
    try:
        if clean_json_response_fn is not None:
            result_json = clean_json_response_fn(result_content)
        else:
            result_json = json.loads(result_content)
    except Exception as e:
        result_json = {"error": f"JSON parsing failed: {e}", "raw": result_content}

    print(f"QnA result for {case_id}:")
    print(json.dumps(result_json, indent=2))

    os.makedirs(save_dir, exist_ok=True)
    out_path = os.path.join(save_dir, f"{case_id}_qna.json")

    result_with_tokens = {
        "qna_result": result_json,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result_with_tokens, f, indent=2, ensure_ascii=False)

    print(f"QnA results saved to {out_path}")

    return result_with_tokens