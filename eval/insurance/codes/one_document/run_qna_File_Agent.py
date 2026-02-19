import os
import json
import re
import time
from openai import OpenAI

class QnAExecutorWithPDF:
    uploaded_files_cache = {} # Class-level cache: MD5 → uploaded OpenAI file_id
    cache_file = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/codes/one_document/pdf_upload_cache.json"
    def __init__(self, questions_list, llm_model="gpt-5-mini", openai_api_key=None, save_base_dir="sample"):
        # Initialize with questions, model name, and API key
        self.questions_list = questions_list
        self.formatted_questions = self.format_questions()
        self.model = llm_model  # use this everywhere (e.g., "gpt-5" or "gpt-5-mini")
        self.openai_api_key = openai_api_key
        self.save_base_dir = save_base_dir
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self._load_cache()
        self.pdf_base_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/policy_answer_real"

        self.md5_to_pdf = {
            "c5c2b854957d06467835e88a963d0c82": "BCBS_FEP_20402 Germline Genetic Testing for.pdf",
            "8340e5b0ce4959eccfb2cb295edb47f3": "BCBS_FEP_20459 Genetic Testing for Developmental.pdf",
            "d5e9701c13de1dca302ad0ce45524039": "BCBS_FEP_204102 Whole Exome and.pdf",
            "36bb5264dda1b2027dcdfdd32a714204": "Cigna_MOL.TS_.306.C_Whole_Genome_Sequencing_Cigna_eff01.01.2025_pub09.10.2024.pdf",
            "626eac4d60df057ea93ece78f8cc3dfc": "Cigna_MOL.TS_.238.A_BRCA_Analysis_eff01.01.2025_pub09.10.2024_1.pdf",
            "c69485372670ce1d12aa8f61d83a06fd": "United Healthcare_genetic-testing-hereditary-cancer.pdf",
            "8a7d5f974648c666b635eae9e03277e7": "United Healthcare_chromosome-microarray-testing.pdf",
            "dd74cd39fca15b7b0888b16ce1da2014": "Cigna_MOL.TS_.150A_CMA_for_Developmental_Disorders_and_Prenatal_Diagnosis_eff01.01.2025_pub09.10.2024_1.pdf",
            "4fadf6b3ca9d4d08131cb31365e3aa7d": "United Healthcare_whole-exome-and-whole-genome-sequencing.pdf",
            "ad2eb3a750b767e32ff847032f0e8e03": "Cigna_MOL.TS_.235.C_Whole_Exome_Sequencing_Cigna_eff01.01.2025_pub09.20.2024.pdf",
            "49b51c0399e5563339f32a9f24f20641": "Cigna_MOL.TS_.344.A_Chromosomal_Microarray_Solid_Tumors_eff01.01.2025_pub09.11.2024_0.pdf"
        }
        self.cached_prefix = self.build_cached_prefix()

    def _load_cache(self):
        """Load uploaded file cache from JSON"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    QnAExecutorWithPDF.uploaded_files_cache = json.load(f)
                print(f"📦 Loaded {len(self.uploaded_files_cache)} cached file IDs")
            except Exception as e:
                print(f"❌ Failed to load cache: {e}")
        else:
            print("❌ Cache file does not exist")
    
    def get_pdf_path_from_case(self, case_data):
        '''Resolve the expected PDF path from case's MD5'''
        if 'expected_md5' not in case_data:
            raise ValueError(f"Case {case_data.get('id', 'Unknown')} does not have 'expected_md5' field")

        md5_hash = case_data['expected_md5']

        # Just in case md5 Unknown cases
        if md5_hash == "UNKNOWN":
            print(f"⚠️ {case_data.get('id', 'Unknown')}: UNKNOWN MD5 - proceeding without PDF")
            return None, md5_hash

        if md5_hash not in self.md5_to_pdf:
            print(f"⚠️ MD5 hash {md5_hash} not found in mapping - proceeding without PDF")
            return None, md5_hash

        pdf_filename = self.md5_to_pdf[md5_hash]
        pdf_path = os.path.join(self.pdf_base_path, pdf_filename)
        if not os.path.exists(pdf_path):
            print(f"⚠️ PDF file does not exist: {pdf_path} - proceeding without PDF")
            return None, md5_hash

        print(f"✅ {case_data['id']}: Found PDF - {pdf_filename} - {md5_hash}")
        return pdf_path, md5_hash

    def upload_pdf_to_openai(self, pdf_path, md5_hash):
        '''Upload PDF to OpenAI; reuse cached file if available'''
        if md5_hash in self.uploaded_files_cache:
            file_id = self.uploaded_files_cache[md5_hash]
            print(f"✅ Utilizing cached file: {file_id} (MD5: {md5_hash})")
            return file_id
        try:
            with open(pdf_path, "rb") as f:
                uploaded_file = self.openai_client.files.create(
                    file=f,
                    purpose="assistants"  # generic purpose; just need file_id for Responses input_file
                )
            self.uploaded_files_cache[md5_hash] = uploaded_file.id
            
            try:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.uploaded_files_cache, f, indent=2)
            except:
                pass
            print(f"✅ OpenAI upload succeeded: {uploaded_file.id} (MD5: {md5_hash})")
            return uploaded_file.id
        
        except Exception as e:
            print(f"❗ OpenAI upload failed: {e}")
            raise

    def _enqueue_batch_line(self, custom_id, input_content, jsonl_path):
        """Responses API용 배치 라인 추가"""
        body = {
            "model": self.model,
            "input": input_content,  # [{"role": "user", "content": [...]}] 형태
            "prompt_cache_key": "qna-template-v1"
        }
        line = {
            "custom_id": custom_id,
            "method": "POST", 
            "url": "/v1/responses",
            "body": body
        }
        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def prepare_batch_for_cases(self, case_list):
        """여러 케이스를 배치용 JSONL로 준비"""
        jsonl_path = os.path.join(self.save_base_dir, "batch_qna_requests.jsonl")
        os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)

    # 기존 JSONL 파일 초기화
        if os.path.exists(jsonl_path):
            os.remove(jsonl_path)
    
        for case_data in case_list:
            try:
                case_id = case_data['id']
                patient_info = case_data['patient_info']
            
                pdf_path, md5_hash = self.get_pdf_path_from_case(case_data)
                if not pdf_path:
                    continue
                
                file_id = self.upload_pdf_to_openai(pdf_path, md5_hash)
                prompt_text = self.build_qna_input_cached(patient_info, self.cached_prefix)
            
                input_content = [{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt_text},
                        {"type": "input_file", "file_id": file_id}
                    ],
                }]
            
                self._enqueue_batch_line(case_id, input_content, jsonl_path)
                print(f"✅ {case_id}: Added to batch")
            
            except Exception as e:
                print(f"❗ {case_data.get('id', 'Unknown')}: Failed to add to batch - {e}")
    
        return jsonl_path

    def submit_batch(self, jsonl_path):
        """배치 job 제출"""
        upload = self.openai_client.files.create(
            file=open(jsonl_path, "rb"), 
            purpose="batch"
        )
        batch = self.openai_client.batches.create(
            input_file_id=upload.id,
            endpoint="/v1/responses", 
            completion_window="24h"
        )
    
        log_dir = os.path.join(self.save_base_dir, "batch_logs")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "batch_id.txt"), "w") as f:
            f.write(batch.id)
    
        print(f"✅ Batch submitted: {batch.id}")
        return batch.id
    
    def format_question_block(self, q, indent=2):
        '''Format a single question with its options'''
        indent_str = " " * indent
        question_line = f"{q['question']}"
        question_line += f"\n{indent_str}Options: {', '.join(q['options'])}"
        return question_line

    def format_questions(self):
        '''Join all formatted questions with IDs and spacing'''
        return "\n\n".join([
            f"{q['id']}. {self.format_question_block(q)}"
            for q in self.questions_list
        ])

    def clean_json_response(self, response_text):
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
    
    def build_cached_prefix(self):
        '''Build a cached prompt prefix for QnA'''
        return f"""
Answer the questions based strictly on the provided patient information and insurance policy documents.
You will be given:

1. Patient clinical information.
2. Official insurance policy document text (strictly use this policy content for insurance coverage decision making).

Instructions:
- Answer all questions strictly based on the patient clinical information and insurance policy document provided.
- Do NOT refer to general guidelines or policies from other insurance providers.
- If policy document does not clearly specify rules, you MAY use patient's clinical information to infer answers carefully.
- Do NOT assume coverage criteria from other insurers or general clinical guidelines unless explicitly stated in the policy.
- Provide brief reasoning for each answer.
- Output answers in JSON format ONLY.

Focus on sections for uploaded policy document:
- **Age criteria**
- **Medical necessity criteria**
- **Prior test criteria**
- **Family history information** 
- **Related CPT codes**
- **Coverage criteria**
- **Counseling / Provider criteria**

Questions to answer:
{self.formatted_questions}

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

    def build_qna_input_cached(self, patient_info, cached_prefix):
        """Build the variable part and combine with cached prefix."""
        return cached_prefix + f"""Patient Information:
{patient_info}
"""

    def run_qna_with_pdf(self, case_data):
        """run QnA with PDF document using OpenAI API."""
        case_id = case_data['id']
        patient_info = case_data['patient_info']
        
        try:
            pdf_path, md5_hash = self.get_pdf_path_from_case(case_data)
            if not pdf_path:
                return None
            file_id = self.upload_pdf_to_openai(pdf_path, md5_hash)
            prompt_text = self.build_qna_input_cached(patient_info, self.cached_prefix)
            
            resp = self.openai_client.responses.create(
                model=self.model,                
                input=[
                    {
                        "role": "system",
                        "content": [
                            {"type": "input_text", "text": "You are a clinical insurance assistant specializing in genetic testing coverage policies."}
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt_text},
                            {"type": "input_file", "file_id": file_id}
                        ]
                    }
                ]
            )

            if hasattr(resp, 'usage') and resp.usage:
                input_tokens = resp.usage.input_tokens
                output_tokens = resp.usage.output_tokens
                total_tokens = resp.usage.total_tokens
            else:
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0

            # Extract text from Responses result
            result_content = getattr(resp, "output_text", None)
            if not result_content and getattr(resp, "output", None):
                try:
                    result_content = resp.output[0].content[0].text.value
                except Exception:
                    pass
            if not result_content:
                raise ValueError("No text found in Responses API result.")


            result_json = self.clean_json_response(result_content)
            final_result = dict(result_json)
            final_result["md5_hash"] = md5_hash

            final_result["token_usage"] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }

            save_dir = os.path.join(self.save_base_dir, "qna_results")
            os.makedirs(save_dir, exist_ok=True)
            filename = os.path.join(save_dir, f"{case_id}_{self.model}_qna_result_final.json")

            with open(filename, "w") as f:
                json.dump(final_result, f, indent=2)
            print(f"✅ QnA result saved to {filename}")
            return final_result
        
        except Exception as e:
            print(f"❗ {case_id} Error during QnA: {e}")
            return None

if __name__ == "__main__":
    from dotenv import load_dotenv
    path = '/home/cptaswadu/new-rescue/RESCUE-n8n'
    load_dotenv(dotenv_path=os.path.join(path, ".env"))
    openai_api_key = os.getenv("OPEN_AI_API_KEY")

    dataset_path="/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/sample_qna_free_text.json"
    questions_file_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/Insurance_Genetic_Testing_QA.json"
    with open(questions_file_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    questions_list = questions_data["questions"]

    executor = QnAExecutorWithPDF(
        questions_list=questions_list,
        llm_model="gpt-5-mini",
        openai_api_key=openai_api_key,
        save_base_dir="test_run2"
    )

    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    case_ex = cases[:2]

    jsonl_path = executor.prepare_batch_for_cases(case_ex)
    print(f"Batch JSONL created: {jsonl_path}")
    
    batch_id = executor.submit_batch(jsonl_path)
    print(f"Batch submitted with ID: {batch_id}")

    #for case in case_ex:
        #out = executor.run_qna_with_pdf(case)
        #if out is not None:
            #print(f"✅ {case['id']} completed")
        #else:
            #print(f"⚠️ {case.get('id', 'Unknown')} skipped (no PDF or error)")
