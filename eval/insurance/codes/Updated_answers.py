# import library
import random
import json
from collections import defaultdict
from openai import OpenAI
import pandas as pd
import numpy as np
import csv
import os
from dotenv import load_dotenv

load_dotenv('/home/cptaswadu/new-rescue/RESCUE-n8n/.env')
client = OpenAI(api_key=os.getenv('OPEN_AI_API_KEY'))

insurance_options = ["BCBS_FEP", "Cigna", "UHC"]
test_options = ["BRCA1/2", "WES", "WGS", "CMA", "CMA_developmental_disorder", "CMA_tumor"]
# q0 - what kind of genetic tests
# genetic_tests_options = {
#     "BCBS_FEP": ["BRCA1/2", "WES", "WGS", "CMA"],
#     "UHC": ["BRCA1/2", "WES", "WGS", "CMA"],
#     "Cigna": ["BRCA1/2", "WES", "WGS", "CMA_developmental_disorder", "CMA_tumor"]
# }

# q1 - age criteria
age_categories = [(-1,0), (0,0), (0,17), (0,18), (0,21), (18,45), (46,65), (66,75)]
def generate_age_in_category(age_categories):
    selected_category = age_categories
    if selected_category == (-1,0):
        # I want a random weeks (prenatal)
        weeks = random.randint(10,39)                    
        return -1, f"{weeks} weeks gestation"
    elif selected_category == (0,0):
        weeks = random.randint(0,8)
        return 0, f"{weeks} weeks age"
    else:
        if selected_category == (0,0):
            # pronatal cases
            months = random.randint(3, 12)
            return 0, f"{months} months age"
        else:
            # other age ranges
            years = random.randint(selected_category[0], selected_category[1])
            return years, f"{years} years age" 
         
def is_in_age_range(age_value, target_ranges):
    age_value = int(age_value)
    for min_age, max_age in target_ranges:
        if min_age == 0 and max_age == 0:
            if age_value == 0:
                return True
        elif min_age <= age_value <= max_age:
            return True
    return False


# q2 - order providers
order_providers_options = ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician", "Obstetrician", "Gynecologist", "Cardiologist", "Pediatric Neurologist", "Primary Care Physician", "General Pediatrician", "Nurse Practitioner", "Family Medicine Physician", "General Practitioner"]

# q3 - clinical indications
# category to clinical indications mapping
q3_cat_ind = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_ind_q3.csv')
# category to insurance coverage (test - insurance company) mapping
q3_cat_test_ins = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_test_ins_q3.csv')
# merge two dataframes on 'Category' column: category, Indications, insurance coverage
q3_merged = pd.merge(q3_cat_ind, q3_cat_test_ins, on='Category', how='outer', suffixes=('_ins', '_ind'))

uhc_diagnosed_age_indications = {
    "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age": 18,
    "Epileptic encephalopathy with onset before three years of age": 3,
    "Unexplained epileptic encephalopathy (onset before three years of age) and no prior epilepsy multigene panel testing performed": 3,
    "Significant hearing or visual impairment diagnosed by 18 years of age": 18
}

cigna_diagnosed_age_indications = {
    "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age": 18,
    "Epileptic encephalopathy with onset before three years of age": 3,
    "Unexplained epileptic encephalopathy (onset before three years of age) and no prior epilepsy multigene panel testing performed": 3,
    "Global developmental delay": 5,
    "Global Developmental Delay": 5
}

# q4 - prior testing
prior_testing_options = ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing", "No prior testing"]

# q5 - family history
# category to family history mapping
q5_cat_hist = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_ind_q5.csv')
# category to insurance coverage (test - insurance company) mapping
q5_cat_test_hist = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_test_ins_q5.csv')
# merge two dataframes on 'Category' column: category, Family history, insurance coverage
q5_merged = pd.merge(q5_cat_hist, q5_cat_test_hist, on='Category', how='outer', suffixes=('_ins', '_hist'))

# q6 - genetic counselor
genetic_counselor_options = ["Saw a genetic counselor before testing and will visit after results are received", "Saw a genetic counselor multiple times", "discussed with a genetic specialist", "No genetic counseling conducted", "No mention of genetic counseling", "Declined genetic counseling"]

# q7 - CPT codes
cpt_codes_options = ["81162", "81277", "81228", "81415", "81425", "Not Specified"]

uhc_diagnosed_age_indications = {
    "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age": 18,
    "Epileptic encephalopathy with onset before three years of age": 3,
    "Significant hearing or visual impairment diagnosed by 18 years of age": 18
}

cigna_diagnosed_age_indications = {
    "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age": 18,
    "Epileptic encephalopathy with onset before three years of age": 3
}

# answer sampling
def get_answers(sample_patient_dict):
    case_id, insurance, genetic_tests, age, age_string, order_provider, clinical_indication, prior_testing, family_history, genetic_counselor, cpt_code = sample_patient_dict.values()
    q0, q1, q2, q3, q4, q5, q6, q7, q8 = ["Not Specified"] * 9  # Initialize all questions with None
    
    # q0 - genetic tests
    if genetic_tests.startswith('CMA'):
        q0 = "CMA" # group all CMA together since CMA has 3 types (CMA, CMA_developmental_disorder, CMA_tumor)
    else:
        q0 = genetic_tests # BRCA1/2, WES, WGS
    
    # q1 - age criteria
    if insurance == "BCBS_FEP":
        if genetic_tests in ["WES", "WGS"]:
            if age <= 18:
                q1 = "Yes"
            else:
                q1 = "No"

        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"

    if insurance == "UHC":
        if genetic_tests in ["WES", "WGS"]:
            if age == -1:
                if genetic_tests == "WES":
                    q1 = "Yes"  # prenatal case included
                else:
                    q1 = "No"   # WGS prenatal case not included
            elif clinical_indication in uhc_diagnosed_age_indications:
                required_age = uhc_diagnosed_age_indications[clinical_indication]
                if age <= required_age:
                    q1 = "Yes"
                else:
                    q1 = "Not Specified"

            else:
                q1 = "Not Specified"

        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"

    if insurance == "Cigna":
        if genetic_tests in ["WES", "WGS"]:
            if age == -1:
                if genetic_tests == "WES":
                    q1 = "Yes"  # prenatal case included
                else:
                    q1 = "No"   # WGS prenatal case not included
            elif clinical_indication in cigna_diagnosed_age_indications:
                required_age = cigna_diagnosed_age_indications[clinical_indication]
                if age <= required_age:
                    q1 = "Yes"
                else:
                    q1 = "Not Specified"
            else:
                if age < 21:
                    q1 = "Yes"
                else:
                    q1 = "No"

        elif genetic_tests == "BRCA1/2":
            if age < 18:
                q1 = "No"
            else:
                q1 = "Yes"

        elif genetic_tests == "CMA_developmental_disorder":
            if age == 0: # prenatal/pronatal
                q1 = "Yes"
            else:
                q1 = "No"

        # no age criteria for CMA_tumor

    # q2 - order provider (only UHC WES/WGS has specific criteria)
    if insurance == "UHC":
        if genetic_tests in ["WES", "WGS"]:
            q2 = "Yes" if order_provider in ["Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"    
    
    # q3 - clinical indication
    # 1. Perfect match: Test + Indication + Insurance all exist
    mask_test = (q3_merged['Test'] == genetic_tests)
    mask_ind  = (q3_merged['Indication'] == clinical_indication)
    mask_ins  = (q3_merged['Insurance'] == insurance)

    # 1) Full match: Test + Indication + Insurance all match
    full_match = len(q3_merged[mask_test & mask_ind & mask_ins]) > 0

    # 2) Medically appropriate: Test + Indication combination exists
    medically_appropriate = len(q3_merged[mask_test & mask_ind]) > 0

    # 3) Insurance covers the test: Test + Insurance combination exists
    test_insurance_combo = len(q3_merged[mask_test & mask_ins]) > 0

    # 4) Not Specified condition: Test + Indication exists but insurance differs
    not_specified_condition = medically_appropriate and (not full_match)

    # Decision logic
    if full_match:
        q3 = "Yes"
    elif not medically_appropriate or not test_insurance_combo:
        # Either the indication is not appropriate OR the insurance does not cover the test
        q3 = "No"
    elif not_specified_condition:
        q3 = "Not Specified"
    else:
        # Safety fallback
        q3 = "Not Specified"

    # q4 - Prior Testing (For WES/WGS/CMA_developmental_disorder only)
    if genetic_tests in ["WES", "WGS"]:
        q4 = "Yes" if prior_testing in ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing"] else "No"
    if insurance == "Cigna" and genetic_tests == "CMA_developmental_disorder":
        q4 = "Yes" if prior_testing in ["FISH testing", "Karyotype testing"] else "No"

    # q5 - family history
    mask_test = (q5_merged['Test'] == genetic_tests)
    mask_fh   = (q5_merged['Family history'] == family_history)
    mask_ins  = (q5_merged['Insurance'] == insurance)

    # 1) Full match: Test + Family history + Insurance all match
    full_match = len(q5_merged[mask_test & mask_fh & mask_ins]) > 0

    # 2) Family-history appropriate: Test + Family history combination exists
    #family_appropriate = len(q5_merged[mask_test & mask_fh]) > 0

    # 3) Insurance covers the test: Test + Insurance combination exists
    test_insurance_combo = len(q5_merged[mask_test & mask_ins]) > 0

    # 4) Not Specified condition: Test + Family history exists but insurance differs
    #not_specified_condition = len(test_insurance_combo) == 0

    # Decision logic (flat, no nesting)
    if full_match:
        q5 = "Yes"
    elif test_insurance_combo:
    # Either the family history is not appropriate OR the insurance does not cover the test
        q5 = "No"
    #elif not_specified_condition:
    #    q5 = "Not Specified"
    else:
    # Safety fallback
        q5 = "Not Specified"

    # q6 - counselor (For BCBS_FEP BRCA1/2, WES, WGS; Cigna BRCA1/2, CMA_developmental_disorder only)
    if insurance == "BCBS_FEP" and genetic_tests in ["BRCA1/2", "WES", "WGS"]:
        q6 = "Yes" if genetic_counselor in ["Saw a genetic counselor before testing and will visit after results are received", 
                                         "Saw a genetic counselor multiple times", 
                                         "discussed with a genetic specialist"] else "No"
    elif insurance == "Cigna" and genetic_tests in ["BRCA1/2", "CMA_developmental_disorder"]:
        q6 = "Yes" if genetic_counselor in ["Saw a genetic counselor before testing and will visit after results are received", 
                                         "Saw a genetic counselor multiple times", 
                                         "discussed with a genetic specialist"] else "No"

    # q7 - CPT codes mapping
    cpt_mapping = {
    "WES": "81415",
    "WGS": "81425", 
    "BRCA1/2": "81162",
    "CMA": "81228",
    "CMA_developmental_disorder": "81228",
    "CMA_tumor": "81277"
}

    # q7 - cpt code (BCBS_FEP does not mention cpt code)
    if insurance in ["UHC", "Cigna"]:
        if q0 == "CMA":
            if insurance == "UHC" and genetic_tests == "CMA_tumor": # there is no CMA_tumor in UHC
                q7 = cpt_mapping.get("CMA")
            elif insurance == "Cigna" and genetic_tests == "CMA":
                q7 = "Not Specified"  # Cigna does not have CMA itself in the policy
            else:
                q7 = cpt_mapping.get(genetic_tests)
        else:
            q7 = cpt_mapping.get(q0) # BRCA1/2, WES, WGS cpt codes are the same across UHC, Cigna

    # q8 - final decision
    all_answers = [q1, q2, q3, q4, q5, q6] 
    # if one of the answers is "No", then q8 is "No"
    if "No" in all_answers:
        q8 = "No"
    else:
        q8 = "Yes"
                            
    return {
        sample_patient_dict.get("case_id"): {
            'Q0': q0,
            'Q1': q1,  
            'Q2': q2,  
            'Q3': q3,  
            'Q4': q4,  
            'Q5': q5,  
            'Q6': q6,  
            'Q7': q7,  
            'Q8': q8,
            'sample_patient_dict': sample_patient_dict
        }    
    } 

# random.seed(42)

# number_of_samples = 20000  # Number of sample patients to generate
# idx = 0 # initial index
# samples = [] # empty list to store sample patients
# # Generate sample patients
# while idx < number_of_samples:
#     case_id = f"Case{idx + 1}"  # starting form 1, make case_id
#     age_years, age_string = generate_age_in_category(random.choice(age_categories))
#     sample_patient = {
#         "case_id": case_id,
#         "insurance": random.choice(insurance_options),
#         "genetic_tests": random.choice(test_options),
#         "age_years": age_years,
#         "age_string": age_string,
#         "order_provider": random.choice(order_providers_options),
#         "clinical_indication": random.choice(q3_merged['Indication']),
#         "prior_testing": random.choice(prior_testing_options),  
#         "family_history": random.choice(q5_merged['Family history']),
#         "genetic_counselor": random.choice(genetic_counselor_options),
#         "cpt_code": random.choice(cpt_codes_options)
#     }
    
#     answer = get_answers(sample_patient)
#     samples.append(answer)
#     idx += 1

dataset_dir = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
# if not os.path.exists(dataset_dir):
#     os.makedirs(dataset_dir)
# with open(f'{dataset_dir}/samples.json', 'w') as f:
#     json.dump(samples, f, indent=4)

# def negative_sample_balanced_dataset(realistic_samples, target_size, test_proportions=None):
#     test_groups = defaultdict(list)
#     for s in realistic_samples:
#         case_data = list(s.values())[0]
#         test_name = case_data["Q0"]
#         test_groups[test_name].append(s)

#     test_counts = {test: len(group) for test, group in test_groups.items()}
#     total_realistic = sum(test_counts.values())
    
#     if test_proportions is None:
#         test_proportions = {test: count/total_realistic for test, count in test_counts.items()}

#     balanced_samples = []
#     count_yes = sum(1 for s in realistic_samples for case_data in s.values() if case_data["Q8"] == "Yes")
#     p_q8_yes = count_yes / len(realistic_samples) if len(realistic_samples) > 0 else 0
    
#     def _compute_q8_weight(sample, p_q8_yes, epsilon=1e-6):
#         case_data = list(sample.values())[0]
#         if case_data["Q8"] == "Yes":
#             return 1 / (p_q8_yes + epsilon)
#         else:
#             return 1 / (1 - p_q8_yes + epsilon)
    
#     def _weighted_sample_without_replacement(population, weights, k):
#         if k >= len(population):
#             return population.copy()
        
#         selected = []
#         remaining_pop = population.copy()
#         remaining_weights = weights.copy()
        
#         for _ in range(k):
#             total_weight = sum(remaining_weights)
#             probabilities = [w / total_weight for w in remaining_weights]
#             chosen_idx = random.choices(range(len(remaining_pop)), weights=probabilities, k=1)[0]
#             selected.append(remaining_pop.pop(chosen_idx))
#             remaining_weights.pop(chosen_idx)
        
#         return selected
    
#     for test, proportion in test_proportions.items():
#         test_group = test_groups.get(test, [])
#         if not test_group:
#             continue

#         weights = [_compute_q8_weight(s, p_q8_yes) for s in test_group]
#         k = int(target_size * proportion)
#         k = min(k, len(test_group))

#         selected = _weighted_sample_without_replacement(test_group, weights, k)
#         balanced_samples.extend(selected)
    
#     print(f"Actual sampled: {len(balanced_samples)}")
#     return balanced_samples

# test_ratios = {
#     "WES": 0.4,
#     "WGS": 0.2,
#     "BRCA1/2": 0.3,
#     "CMA": 0.1
# }

# balanced_samples = negative_sample_balanced_dataset(samples, target_size=200, test_proportions=test_ratios)

# # Save the balanced samples to a JSON file
dataset_dir = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
# if not os.path.exists(dataset_dir):
#     os.makedirs(dataset_dir)
# with open(f'{dataset_dir}/balanced_samples.json', 'w') as f:
#     json.dump(balanced_samples, f, indent=4)

# # Check q8 balance
# def print_q8_balance(dataset):
#     total = len(dataset)
#     yes = sum(1 for s in dataset for case_data in s.values() if case_data["Q8"] == "Yes")
#     print(f"Q8 Yes: {yes/total:.2f}, No: {(total - yes)/total:.2f}")

# print_q8_balance(balanced_samples)

def evaluate_and_generate(sample_patient_dict, model="gpt-5-nano"):
    """
    1) Use gpt-5-mini to evaluate realism and (if realistic) generate a one-paragraph vignette.
    2) Return the result as [case_id, genetic_tests, realistic(bool), text].
       - If realistic: text = vignette paragraph
       - If unrealistic: text = "NO — <one-sentence reason>"
    """

    # Remove fields we do NOT want to surface in the prompt to the model
    hidden_keys = {'cpt_code', 'case_id'}
    facts_for_model = {k: v for k, v in sample_patient_dict.items() if k not in hidden_keys}

    # System message: role + strict output contract
    system_prompt = ("""
         You are a clinical evaluator and medical writer. First decide if the case is realistic.

If the case is realistic, you MUST write exactly one paragraph of natural clinical prose (no labels/placeholders).
If the case is unrealistic, you MUST write exactly one concise sentence explaining why.

Your output MUST be EXACTLY one of the two formats below:

YES
<the free-text paragraph itself on this next line>

NO
<the one-sentence reason itself on this next line>

Do NOT include any other headings, labels, field names, bullets, or code blocks.
Do NOT literally write the words “Free-text”, “vignette”, or any angle-bracket placeholders.
Do NOT invent diagnoses/results, and do NOT include CPT codes or internal IDs.
Write polished U.S. clinical English in one cohesive paragraph. 
Do NOT echo UI/field tokens or option labels (e.g., age_years, case_id, cpt_code, insurance_plan, genetic_tests); remove any garbled characters or mojibake (e.g., “??”, “�”).  
                     """
    )

    # User prompt with decision rules first, then generating rules
    user_prompt = f"""
DECISION RULES (flag ONLY critical impossibilities; allow atypical but plausible cases):
- Test–indication(including family history): Allow mismatches and suboptimal choices unless biologically/temporally impossible. Do NOT reject just because a different (more appropriate) test exists (e.g., CMA_tumor vs germline) if the scenario is still possible.
- Sex–condition impossibilities: male ↔ ovarian/uterine/cervical/pregnancy; female ↔ prostate/testicular.
- Try to consider whether indication is possible given the patient's age and clinical context. (e.g., 73 years old with still birth is not possible) 
Age–provider: consider patient information and provider specialties when evaluating cases but only flag when truly impossible:
  • Adult managed by a neonatologist/pediatrician → NO.
  • Neonate/infant (<1 year) managed by a geriatrician/internal-medicine-only specialist → NO.
  • child/adolescent with a neonatologist is not ALLOWED → NO.
- Adult congenital labeling: In adults (≥18), indications explicitly labeled “multiple congenital anomalies” or other pediatric-only labels are NOT allowed as current indications → NO.
- Cancer test contextual purity: For adult hereditary cancer testing (e.g., BRCA1/2), if the narrative mixes in pediatric-only neuro/ND indications (e.g., hypotonia in infancy) as part of the same evaluation context, mark → NO (contextual inconsistency), regardless of family history.
- Prenatal phrasing gate: Any gestational/fetal phrasing (“at X weeks’ gestation”, “fetus”, “prenatal”) is valid ONLY when age_years == -1; otherwise → NO.
- Prenatal neuro terms: In prenatal cases (age_years == -1), ANY mention of neurodevelopmental/neuropsychiatric/behavioral outcomes or labels is NOT allowed → NO.
  (trigger terms: neurodevelopmental, intellectual disability/ID, developmental delay/DD, regression, ASD/autism, ADHD, learning disability, language delay, global delay, cognitive impairment, dystonia, ataxia, movement disorder)
- Fetal test scope: For a fetus (age_years == -1), karyotype/CMA/WES/WGS only; adult-onset cancer susceptibility single-gene tests (e.g., BRCA1/2, Lynch/MMR genes) → NO.
- Onset timing: Onset age must be < current age (EXCEPTION: prenatal fetus with age_years == -1). Phrases like “lifelong/since infancy” are allowed if consistent. Please distinguish between weeks and years.
- Age–indication contradictions: Pediatric-only indications (e.g., failure to thrive, childhood short stature, microcephaly, congenital anomalies) are unrealistic in clear adults (e.g., 66 or 74 years) → NO. Likewise, adult-only indications are unrealistic in neonates/infants → NO.
- Prenatal test scope: For a fetus, allowable genetic tests include karyotype, CMA, WES/WGS. Adult-onset cancer susceptibility single-gene testing on the fetus (e.g., BRCA1/2, Lynch/MMR genes) is unrealistic → NO.
- Family history: use specific kinship terms (e.g., “mother”, “father”, “sibling”) and avoid vague terms like “first-degree”/“second-degree”.
- Do NOT reject just because the ordering provider is not the most typical, unless it hits the “Age–provider” NO rules above.
CALIBRATION EXAMPLES (how to judge):
  • YES (allowed): 66-year-old with conjugated hyperbilirubinemia evaluated by neurologist; CMA ordered; prior FISH non-diagnostic; family history pancreatic cancer; UHC insurance. 
  • NO (prenatal test scope): 19-week fetus planned for BRCA1/2 testing due to family variant → unrealistic (adult-onset cancer susceptibility testing on fetus).
  • NO (age–indication contradiction): 74-year-old with “failure to thrive/childhood short stature/microcephaly”.
  • NO (age–indication contradiction): Prenatal has neurodevelopmental risk factors.


OUTPUT FORMAT (strict):
If YES, output:
YES
<one-paragraph Free-text>
If NO, output:
NO
<one-sentence reason>

FREE-TEXT RULES (apply ONLY if YES):
- One cohesive paragraph narrative as clinical notes, U.S. clinical English, third-person; no lists or bullet-like enumerations; avoid semicolons.
- Paraphrase any option labels into natural clinical prose; do NOT mirror UI tokens or field names (e.g., age_years, case_id, cpt_code, insurance_plan, genetic_tests).
- Clinical indication: express as natural prose; expand shorthand/acronyms on first use (e.g., “chromosomal microarray (CMA)"), then use the acronym thereafter. If multiple severities appear, choose a single appropriate descriptor.
- Family history: use a specific kinship term (mother/father/brother/sister/uncle/aunt/cousin). Never write “first-degree/second-degree”; if only degree is provided, infer a plausible kinship consistent with that degree.
- Prior testing: if present, NAME it and state it was nondiagnostic or similar meaning; if empty/“Not Specified,” state it as no prior testing information.
- Ordering provider & genetic counselor: integrate naturally (e.g., “referred by neurology,” “pre-test counseling completed with plans for post-test follow-up”).
- Genetic test(s): mention naturally (e.g., “BRCA1/2 testing,” “WES,” “WGS”) without repeating UI labels.
- Insurance: if provided, use the exact insurer and plan names, woven into prose (e.g., “with coverage through the Blue Cross Blue Shield Federal Employee Program (FEP)”); never invent names; if missing, omit.
- Prenatal phrasing (only if the case is realistic and prenatal by rules): frame findings as **risk/concern/evaluation for possible** postnatal outcomes based on fetal imaging; do NOT assert a present diagnosis in utero.
- Style hygiene: avoid placeholders or meta-words (“Free-text”, “vignette”, angle-bracket templates); normalize punctuation; remove mojibake/garbled characters (e.g., “non?멶iagnostic” → “nondiagnostic”).

FACTS (structured; do not echo keys/labels):
{facts_for_model}
""".strip()

    # Default outputs in case of exception
    realistic = False
    content = ""

    try:
        # Single API call with deterministic behavior
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        raw_output = (resp.choices[0].message.content or "").strip()

        # Normalize common dash variations (em/en dash)
        normalized = raw_output.replace("—", "—").replace("--", "—")

        if normalized.startswith("YES"):
            realistic = True
            # Everything after the first newline is the paragraph
            content = normalized.split("\n", 1)[1].strip() if "\n" in normalized else ""
        elif normalized.startswith("NO"):
            realistic = False
            content = normalized  # Keep "NO — <reason>" as-is
        else:
            realistic = False
            content = f"NO — Unexpected output: {raw_output}"

    except Exception as e:
        realistic = False
        content = f"NO — API error: {e}"

    return realistic, content, sample_patient_dict.get("genetic_tests", "")


def evaluate_and_generate_multiple(sample_patient_dict, model="gpt-5-mini", num_runs=3):
    """
    Run evaluation multiple times and return all results
    """
    results = []
    
    for run in range(num_runs):
        realistic, content, genetic_tests = evaluate_and_generate(sample_patient_dict, model)
        results.append({
            'run': run + 1,
            'realistic': realistic,
            'content': content,
            'genetic_tests': genetic_tests
        })
    
    # Check if all runs are realistic
    all_realistic = all(result['realistic'] for result in results)
    
    # Use the first realistic content, or the first content if none are realistic
    final_content = ""
    for result in results:
        if result['realistic']:
            final_content = result['content']
            break
    if not final_content:
        final_content = results[0]['content']
    
    return all_realistic, final_content, results[0]['genetic_tests'], results

# # List of models to use
# models = ["gpt-5-mini"]

# for model_name in models:
#     print(f"\n=== Processing with {model_name} (3 sets of 200 samples) ===")
    
#     # 각 세트별 결과를 저장할 딕셔너리
#     all_results = {}
    
#     # 3번의 세트 실행
#     for run_set in range(3):
#         print(f"\n--- Run Set {run_set + 1}/3 ---")
        
#         for sample_dict in balanced_samples:
#             case_data = list(sample_dict.values())[0]
#             patient_dict = case_data["sample_patient_dict"]
#             case_id = patient_dict.get('case_id', 'Unknown')
#             print(f"Processing {case_id} (Set {run_set + 1})")
            
#             realistic, content, genetic_tests = evaluate_and_generate(patient_dict, model_name)
            
#             # 결과 저장 구조 초기화
#             if case_id not in all_results:
#                 all_results[case_id] = {
#                     'genetic_tests': genetic_tests,
#                     'runs': []
#                 }
            
#             # 해당 세트 결과 추가
#             all_results[case_id]['runs'].append({
#                 'realistic': realistic,
#                 'content': content
#             })
    
#     # 각 케이스별로 3번 결과 분석
#     final_results = {}
#     for case_id, data in all_results.items():
#         runs = data['runs']
#         all_realistic = all(run['realistic'] for run in runs)
        
#         # 첫 번째 realistic content 찾기
#         final_content = ""
#         for run in runs:
#             if run['realistic']:
#                 final_content = run['content']
#                 break
#         if not final_content:
#             final_content = runs[0]['content']
        
#         final_results[case_id] = {
#             'realistic_all_3': all_realistic,
#             'genetic_tests': data['genetic_tests'],
#             'text': final_content,
#             'run_details': runs
#         }

#     # Include model name in filename
#     model_safe_name = model_name.replace("-", "_")
#     save_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/realistic_results_3sets_{model_safe_name}_200.csv"
    
#     # Save results to CSV file
#     os.makedirs(os.path.dirname(save_path), exist_ok=True)
#     with open(save_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(['case_id', 'genetic_tests', 'realistic_all_3', 'text', 'run1_realistic', 'run2_realistic', 'run3_realistic'])
#         for case_id, data in final_results.items():
#             run_results = [str(run['realistic']) for run in data['run_details']]
#             writer.writerow([
#                 case_id, 
#                 data['genetic_tests'], 
#                 data['realistic_all_3'], 
#                 data['text']
#             ] + run_results)
    
#     print(f"Results saved to {save_path}")

#     # Save raw results (all_results) to CSV file
#     raw_results_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/raw_results_3sets_{model_safe_name}_200.csv"
    
#     with open(raw_results_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow(['case_id', 'genetic_tests', 'set_number', 'realistic', 'content'])
        
#         for case_id, data in all_results.items():
#             for i, run in enumerate(data['runs'], 1):
#                 writer.writerow([
#                     case_id,
#                     data['genetic_tests'],
#                     f"Set {i}",
#                     run['realistic'],
#                     run['content']
#                 ])
    
#     print(f"Raw results saved to {raw_results_path}")

#     # Count cases where all 3 runs are realistic
#     all_realistic_count = sum(1 for data in final_results.values() if data['realistic_all_3'])
#     total_count = len(final_results)
    
#     print(f"All 3 sets realistic: {all_realistic_count}/{total_count}")
    
#     # Append count information to existing CSV file
#     with open(save_path, 'a', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
#         writer.writerow([])  # Empty row
#         writer.writerow(['Summary', '', '', '', '', '', ''])
#         writer.writerow(['Total cases', total_count, '', '', '', '', ''])
#         writer.writerow(['All 3 sets realistic', all_realistic_count, '', '', '', '', ''])
#         writer.writerow(['All 3 sets realistic percentage', f"{all_realistic_count/total_count*100:.1f}%", '', '', '', '', ''])

# print("\n=== All models processing completed ===")


def filter_realistic_samples(balanced_samples, csv_file_path):
    """CSV에서 realistic_all_3=True인 case_id들로 original samples 필터링"""
    
    # CSV에서 realistic_all_3=True인 case_id들 가져오기
    df = pd.read_csv(csv_file_path)
    df = df[df['case_id'].str.startswith('Case', na=False)]
    realistic_case_ids = df[df['realistic_all_3'] == True]['case_id'].tolist()
    
    print(f"📋 Found {len(realistic_case_ids)} case_ids where all 3 runs are realistic from CSV")
    
    # original samples에서 해당 case_id들만 필터링
    filtered_samples = []
    for sample in balanced_samples:
        case_id = list(sample.keys())[0]  # "Case12"
        if case_id in realistic_case_ids:
            filtered_samples.append(sample)
    
    print(f"✅ Filtered to {len(filtered_samples)} samples (all 3 runs realistic)")
    return filtered_samples

# # 각 모델별로 realistic 샘플 필터링 및 저장
# models = ["gpt-5-mini"]  # 현재 한 모델만 사용하는 것 같으니 맞춰서 수정

# for model_name in models:
#     model_safe_name = model_name.replace("-", "_")
#     csv_file_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/realistic_results_3sets_{model_safe_name}_200.csv"  # 3runs 추가
    
#     print(f"\n=== Filtering realistic samples for {model_name} (3 runs all True) ===")
#     realistic_samples = filter_realistic_samples(balanced_samples, csv_file_path)
    
#     # 각 모델별로 realistic 샘플 저장
#     realistic_save_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/realistic_samples_3sets_{model_safe_name}_200.json"  # 3runs 추가
#     with open(realistic_save_path, 'w') as f:
#         json.dump(realistic_samples, f, indent=4)
    
#     print(f"💾 Realistic samples (all 3 runs True) saved to {realistic_save_path}")

# print("\n=== All realistic sample filtering completed ===")


def create_final_freetext_samples(realistic_samples, csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    llm_samples = []
    for sample in realistic_samples:
        case_id = list(sample.keys())[0]
        row = df[df['case_id'] == case_id]
        
        if not row.empty:
            llm_sample = {
                "id": case_id,
                "patient_info": row.iloc[0]['text']
            }
            llm_samples.append(llm_sample)
    
    return llm_samples

# models = ["gpt-5-mini"]  

# for model_name in models:
#     model_safe_name = model_name.replace("-", "_")
#     csv_file_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/realistic_results_3sets_{model_safe_name}_200.csv"  # 3sets 추가

#     print(f"\n=== Creating final freetext samples for {model_name} (from 3 sets) ===")

#     final_samples = create_final_freetext_samples(realistic_samples, csv_file_path)

#     # 각 모델별로 final 샘플 저장
#     final_save_path = f"/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/final_freetext_samples_3sets_{model_safe_name}_200.json"  # 3runs 추가
#     with open(final_save_path, 'w') as f:
#         json.dump(final_samples, f, indent=4)
    
#     print(f"💾 Final freetext samples ({len(final_samples)}) saved to {final_save_path}")

# print("\n=== All final freetext sample creation completed ===")


def remove_cases_from_files(ground_truth_path, freetext_path, cases_to_remove):
    """delete cases from both samples"""
    
    with open(ground_truth_path, 'r') as f:
        ground_truth_data = json.load(f)
    
    # filter cases
    filtered_ground_truth = []
    for item in ground_truth_data:
        case_id = list(item.keys())[0]
        if case_id not in cases_to_remove:
            filtered_ground_truth.append(item)
    
    with open(freetext_path, 'r') as f:
        freetext_data = json.load(f)

    # filter cases
    filtered_freetext = []
    for item in freetext_data:
        case_id = item['id']  
        if case_id not in cases_to_remove:
            filtered_freetext.append(item)
    
    # 3. just in case backup
    with open(ground_truth_path.replace('.json', '_backup.json'), 'w') as f:
        json.dump(ground_truth_data, f, indent=4)
    
    with open(freetext_path.replace('.json', '_backup.json'), 'w') as f:
        json.dump(freetext_data, f, indent=4)

    # 4. Save filtered files - 수정된 부분
    filtered_gt_path = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/filtered_ground_truth.json'
    filtered_ft_path = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/filtered_llm_samples.json'
    
    with open(filtered_gt_path, 'w') as f:
        json.dump(filtered_ground_truth, f, indent=4)  
    
    with open(filtered_ft_path, 'w') as f:
        json.dump(filtered_freetext, f, indent=4)  
    
    print(f"✅ Removed {len(cases_to_remove)} cases from both files")
    print(f"Ground truth: {len(ground_truth_data)} → {len(filtered_ground_truth)}")
    print(f"Freetext: {len(freetext_data)} → {len(filtered_freetext)}")
    print(f"📁 Filtered files saved to dataset directory")

cases_to_remove = ["Case12158", "Case17377", "Case5130", "Case503", "Case7992", "Case11810", "Case16146", "Case364", "Case6342", "Case10493"] 

ground_truth_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/realistic_samples_3sets_gpt_5_mini_200.json"
freetext_path = "/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/results/LLM_QnA/final_freetext_samples_3sets_gpt_5_mini_200.json"

remove_cases_from_files(ground_truth_path, freetext_path, cases_to_remove)

def transform_data_with_md5(input_file, q3_merged):
    policy_mapping = {
        # BCBS_FEP
        ("BCBS_FEP", "BRCA1/2"): "c5c2b854957d06467835e88a963d0c82",
        ("BCBS_FEP", "WES"): "d5e9701c13de1dca302ad0ce45524039", 
        ("BCBS_FEP", "WGS"): "d5e9701c13de1dca302ad0ce45524039",
        ("BCBS_FEP", "CMA"): "8340e5b0ce4959eccfb2cb295edb47f3",
        
        # UHC
        ("UHC", "BRCA1/2"): "c69485372670ce1d12aa8f61d83a06fd",
        ("UHC", "WES"): "4fadf6b3ca9d4d08131cb31365e3aa7d",
        ("UHC", "WGS"): "4fadf6b3ca9d4d08131cb31365e3aa7d",
        ("UHC", "CMA"): "8a7d5f974648c666b635eae9e03277e7",
        
        # Cigna
        ("Cigna", "BRCA1/2"): "626eac4d60df057ea93ece78f8cc3dfc",
        ("Cigna", "WES"): "ad2eb3a750b767e32ff847032f0e8e03",
        ("Cigna", "WGS"): "36bb5264dda1b2027dcdfdd32a714204",
        ("Cigna", "CMA_developmental_disorder"): "dd74cd39fca15b7b0888b16ce1da2014",
        ("Cigna", "CMA_tumor"): "49b51c0399e5563339f32a9f24f20641"
    }
    
    # input data load
    with open(input_file, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    transformed_data = {}
    unknown_count = 0
    
    for case_item in input_data:
        case_id = list(case_item.keys())[0]
        case_data = case_item[case_id].copy()  

        # Extract insurance and genetic_tests
        insurance = case_data["sample_patient_dict"]["insurance"]
        original_genetic_tests = case_data["sample_patient_dict"]["genetic_tests"]
        clinical_indication = case_data["sample_patient_dict"]["clinical_indication"]

        # Transform genetic_tests based on insurance and indication
        if insurance in ["BCBS_FEP", "UHC"] and original_genetic_tests in ["CMA_developmental_disorder", "CMA_tumor"]:
            genetic_tests = "CMA"
        elif insurance == "Cigna" and original_genetic_tests == "CMA":
        # Try to match indication with q3_merged data
            matching_row = q3_merged[q3_merged['Indications'] == clinical_indication]
            if not matching_row.empty and 'CMA_' in matching_row['Test'].iloc[0]:
                genetic_tests = matching_row['Test'].iloc[0]  # CMA_developmental_disorder or CMA_tumor
            else:
            # Random 50:50 selection if no match found
                genetic_tests = random.choice(["CMA_developmental_disorder", "CMA_tumor"])
        else:
            genetic_tests = original_genetic_tests

        # MD5 mapping
        md5_key = (insurance, genetic_tests)
        expected_md5 = policy_mapping.get(md5_key, "UNKNOWN")
        
        # Count UNKNOWN cases
        if expected_md5 == "UNKNOWN":
            unknown_count += 1

        # sample_patient_dict deletion 
        del case_data["sample_patient_dict"]

        # expected_md5 addition
        case_data["expected_md5"] = expected_md5
        
        # add to transformed_data
        transformed_data[case_id] = case_data

        print(f"✅ {case_id}: {insurance} + {genetic_tests} → {expected_md5[:8]}...")

    # Write the transformed data to the output file
    output_path = f"{dataset_dir}/ground_truth.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, indent=4, ensure_ascii=False)

    print(f"Transformed data has been written to {output_path}")
    print(f"Number of UNKNOWN cases: {unknown_count}")

    return transformed_data

def add_md5_by_case_id(input_file):

    with open(input_file, 'r', encoding='utf-8') as f:
        patient_data = json.load(f)

    with open(f"{dataset_dir}/ground_truth.json", 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    
    # Add expected MD5 in each case
    for case in patient_data:
        case_id = case['id']
        
        if case_id in ground_truth and 'expected_md5' in ground_truth[case_id]:
            case['expected_md5'] = ground_truth[case_id]['expected_md5']
        else:
            print(f"❌ {case_id}: Can't find MD5")

    output_path = f"{dataset_dir}/qna_free_text_sample.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patient_data, f, indent=2, ensure_ascii=False)

    print(f"Q&A free text samples have been written to {output_path}")

    return patient_data

transformed_data = transform_data_with_md5(input_file=f"{dataset_dir}/filtered_ground_truth.json", q3_merged=q3_merged)
updated_data = add_md5_by_case_id(input_file=f"{dataset_dir}/filtered_llm_samples.json")

def sample_matching_cases(ground_truth_file, qna_file, sample_size=10):
    """Sampling from both files with matched case_id"""
    

    with open(ground_truth_file, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    
    with open(qna_file, 'r', encoding='utf-8') as f:
        qna_data = json.load(f)
    
    gt_case_ids = set(ground_truth.keys())
    qna_case_ids = set([item['id'] for item in qna_data])
    

    common_case_ids = gt_case_ids.intersection(qna_case_ids)
    print(f"📊 Common cases found: {len(common_case_ids)}")
    
    if len(common_case_ids) < sample_size:
        print(f"⚠️  Warning: Only {len(common_case_ids)} common cases available (requested {sample_size})")
        sample_size = len(common_case_ids)
    
    sampled_case_ids = random.sample(list(common_case_ids), sample_size)
    print(f"🎯 Sampled cases: {sampled_case_ids}")
    
    sampled_gt = {case_id: ground_truth[case_id] for case_id in sampled_case_ids}
    

    sampled_qna = [item for item in qna_data if item['id'] in sampled_case_ids]
    
    gt_sample_path = f"{dataset_dir}/sample_ground_truth.json"
    qna_sample_path = f"{dataset_dir}/sample_qna_free_text.json"
    
    with open(gt_sample_path, 'w', encoding='utf-8') as f:
        json.dump(sampled_gt, f, indent=4, ensure_ascii=False)
    
    with open(qna_sample_path, 'w', encoding='utf-8') as f:
        json.dump(sampled_qna, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sample files created:")
    print(f"   - Ground truth: {gt_sample_path} ({len(sampled_gt)} cases)")
    print(f"   - QnA data: {qna_sample_path} ({len(sampled_qna)} cases)")
    
    return sampled_gt, sampled_qna


sampled_gt, sampled_qna = sample_matching_cases(
    ground_truth_file=f"{dataset_dir}/ground_truth.json",
    qna_file=f"{dataset_dir}/qna_free_text_sample.json",
    sample_size=10
)