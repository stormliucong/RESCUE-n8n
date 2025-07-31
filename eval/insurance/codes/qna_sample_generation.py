import random
import json
import openai
# setup OpenAI API key by loading .env file
from dotenv import load_dotenv
load_dotenv()

insurance_options = ["BCBS_FEP", "Cigna", "UHC"]

# q0 - what kind of genetic tests
genetic_tests_options = genetic_tests_options = {
    "BCBS_FEP": ["BRCA1/2", "WES", "WGS", "CMA"],
    "UHC": ["BRCA1/2", "WES", "WGS", "CMA"],
    "Cigna": ["BRCA1/2", "WES", "WGS", "CMA_developmental_disorder", "CMA_tumor"]
}


# q1 - age criteria
def generate_age_in_category():
    age_categories = [(0,0), (0,17), (0,18), (0,21), (18,45), (46,65), (66,75)]
    selected_category = random.choice(age_categories)
    
    if selected_category == (0,0):
        return 0
    else:
        return random.randint(selected_category[0], selected_category[1])

def is_in_age_range(age_value, target_ranges):
    for min_age, max_age in target_ranges:
        if min_age == 0 and max_age == 0:
            if age_value == 0:
                return True
        elif min_age <= age_value <= max_age:
            return True
    return False


# q2 - order providers
order_providers_options = ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"]

# q3 - clinical indications
clinical_indications_options = ["Developmental delay", "Intellectual disability", "Multiple congenital anomalies", "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age", "Global Developmental Delay", "Epileptic encephalopathy with onset before three years of age", 
                                "Breast cancer diagnosed at age 45 or younger", "Ovarian cancer at any age", "Pancreatic cancer at any age", "Prostate cancer at any age",
                                "Triple-negative breast cancer diagnosed at age 60 or younger", "Apparent nonsyndromic developmental delay or intellectual disability", "Autism spectrum disorder",
                                "Diagnosed with cancer of the central nervous system or soft tissue sarcoma", "congenital cardiac anomaly", "primary peritoneal cancer diagnosis at any age",
                                "Male with breast cancer at any age", "Isolated severe congenital heart disease", "Significant hearing or visual impairment diagnosed by 18 years of age",
                                "Hypotonia or hypertonia in infancy", "Dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality", "Growth abnormality (e.g., failure to thrive, short stature, microcephaly, macrocephaly, or overgrowth)", 
                                "Persistent and severe immunologic or hematologic disorder", "Fetal hydrops of unknown etiology", "Tyrer-Cuzick, BRCAPro, or Penn11 Score of 5% or greater for a BRCA1/2 pathogenic variant", "PREMM5, MMRpro, or MMRpredict Score of 5% or greater for having a Lynch syndrome gene mutation",
                                "Global developmental delay (significant delay in younger children, under age 5 years, in at least two of the major developmental domains: gross or fine motor; speech and language; cognition; social and personal development; and activities of daily living)",
                                "symptoms of a complex neurodevelopmental disorder (epilepsy, self-injurious behavior, reverse sleep-wake cycles, dystonia, ataxia, alternating hemiplegia, neuromuscular disorder)",
                                "severe neuropsychiatric condition (e.g., schizophrenia, bipolar disorder, Tourette syndrome)", "Major congenital cardiac anomaly"]

# q5 - prior testing
prior_testing_options = ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing"]

# q6 - family history
family_history_options = ["Family history of cancer", "Strong family history of breast and ovarian cancer (mother with breast cancer at 40, sister with ovarian cancer at 45)",
            "Ashkenazi Jewish ancestry with family history of BRCA-related cancers",
            "Multiple family members with early-onset breast cancer across generations",
            "Paternal family history of ovarian and pancreatic cancers",
            "Multiple maternal relatives with breast cancer under age 50",
            "close relative with breast cancer under age 50",
            "close relative with ovarian cancer", "close relative with pancreatic cancer", "close relative with prostate cancer", 
            "one Close Blood Relative with history of a Cancer Associated with Lynch Syndrome", "one Close Blood Relative diagnosed with a Primary Solid Tumor (excluding basal or squamous cell skin cancer) at age 40 or younger", 
            "one first degree relative with a history of Two or more different Primary Solid Tumors (excluding basal or squamous cell skin cancer)", "one first degree relative with a history of Neuroendocrine tumor",
            "one second-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome", "one second-degree relative with a history of cancer associated with Lynch Syndrome diagnosed at age 50 or younger",
            "Epithelial ovarian, fallopian tube, or primary peritoneal cancer in at least 1 close blood relative at any age", "Male close blood relative with breast cancer", "Metastatic (radiographic evidence of or biopsy proven disease) or intraductal/cribriform histology, high- or very-high risk prostate cancer in at least 1 close blood relative at any age",
            "First-degree or Seconde-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome", "First-degree or Second-degree relative with Congenital Anomaly",
            "First-degree or Seconde-degree relative with a history of Consanguinity", 
            "First-degree or Seconde-degree relative with a history of Dysmorphic features",
            "First-degree or Seconde-degree relative with a history of Growth abnormality",
            "First-degree or Seconde-degree relative with a history of Autism spectrum disorder",
            "First-degree or Seconde-degree relative with a history of Neuropsychiatric disorder",
            "First-degree or Seconde-degree relative with a history of unexplained developmental regression"
            ]
# q7 - genetic counselor
genetic_counselor_options = ["Saw a genetic counselor before testing and will visit after results are received", "No genetic counseling conducted"]

# q8 - CPT codes
cpt_codes_options = ["81162", "81277", "81228", "81415", "81425", "Not specified"]

# q9 - final decision

def get_answers(sample_patient_dict):
    insurance, genetic_tests, age, order_provider, clinical_indication, prior_testing, family_history, genetic_counselor, cpt_code = sample_patient_dict.values()
    q0, q1, q2, q3, q4, q5, q6, q7, q8 = ["Not Specified"] * 9  # Initialize all questions with None
    
    # q0 - genetic tests

    if genetic_tests.startswith('CMA'):
        q0 = "CMA"
    else:
        q0 = genetic_tests
    
    # q1 - age criteria

    if insurance == "BCBS_FEP":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

    if insurance == "UHC":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

    if insurance == "Cigna":
        if genetic_tests == "WES":
            if is_in_age_range(age, [(0,0), (0,21)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"
        elif genetic_tests == "WGS":
            if is_in_age_range(age, [(0,0), (0,21)]):
                q1 = "Yes"
            else:
                q1 = "No"
        elif genetic_tests == "CMA_developmental_disorder":
            if age == 0: # prenatal/pronatal
                q1 = "Yes"
            else:
                q1 = "No"

    # q2 - order provider

    if insurance == "UHC":
        if genetic_tests == "WES":
            q2 = "Yes" if order_provider in ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"
        elif genetic_tests == "WGS":
            q2 = "Yes" if order_provider in ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"
    
    # q3 - clinical indication

    if genetic_tests == "BRCA1/2":
        q3 = "Yes" if clinical_indication in [
    "Breast cancer diagnosed at age 45 or younger",
    "Ovarian cancer at any age",
    "Pancreatic cancer at any age",
    "Prostate cancer at any age",
    "Triple-negative breast cancer diagnosed at age 60 or younger",
    "Male with breast cancer at any age",
    "Primary peritoneal cancer diagnosis at any age",
    "Tyrer-Cuzick, BRCAPro, or Penn11 Score of 5% or greater for a BRCA1/2 pathogenic variant"
    ] else "No"
        
    if genetic_tests in ["WES", "WGS"]:
        q3 = "Yes" if clinical_indication in [
    "Moderate, severe, or profound Intellectual Disability diagnosed by 18 years of age",
    "Global Developmental Delay",
    "Epileptic encephalopathy with onset before three years of age",
    "Hypotonia or hypertonia in infancy",
    "Dystonia, ataxia, hemiplegia, neuromuscular disorder, movement disorder, or other neurologic abnormality",
    "Symptoms of a complex neurodevelopmental disorder (epilepsy, self-injurious behavior, reverse sleep-wake cycles, dystonia, ataxia, alternating hemiplegia, neuromuscular disorder)",
    "Severe neuropsychiatric condition (e.g., schizophrenia, bipolar disorder, Tourette syndrome)"
    ] else "No"
    
    if insurance == "Cigna":
        if genetic_tests == "CMA_developmental_disorder":
            q3 = "Yes" if clinical_indication in [
                "Major congenital cardiac anomaly",
                "Multiple congenital anomalies",
                "Developmental delay",
                "Intellectual disability",
                "Autism spectrum disorder" 
            ] else "No"
        elif genetic_tests == "CMA_tumor":
            q3 = "Yes" if clinical_indication == "Diagnosed with cancer of the central nervous system or soft tissue sarcoma" else "No"

    # q4 - Prior Testing
    if genetic_tests in ["WES", "WGS"] or (insurance == "Cigna" and genetic_tests == "CMA_developmental_disorder"):
        q4 = "Yes" if prior_testing in ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing"] else "No"

    # q5 family history
    wes_wgs_family_history = [
    "First-degree or Second-degree relative with Congenital Anomaly",
    "First-degree or Seconde-degree relative with a history of Consanguinity",
    "First-degree or Seconde-degree relative with a history of Dysmorphic features",
    "First-degree or Seconde-degree relative with a history of Growth abnormality",
    "First-degree or Seconde-degree relative with a history of Autism spectrum disorder",
    "First-degree or Seconde-degree relative with a history of Neuropsychiatric disorder",
    "First-degree or Seconde-degree relative with a history of unexplained developmental regression"
    ]

    brca_family_history = ["Family history of cancer",
    "Strong family history of breast and ovarian cancer (mother with breast cancer at 40, sister with ovarian cancer at 45)",
    "Ashkenazi Jewish ancestry with family history of BRCA-related cancers",
    "Multiple family members with early-onset breast cancer across generations",
    "Paternal family history of ovarian and pancreatic cancers",
    "Multiple maternal relatives with breast cancer under age 50",
    "close relative with breast cancer under age 50",
    "close relative with ovarian cancer",
    "close relative with pancreatic cancer",
    "close relative with prostate cancer",
    "one Close Blood Relative with history of a Cancer Associated with Lynch Syndrome",
    "one Close Blood Relative diagnosed with a Primary Solid Tumor (excluding basal or squamous cell skin cancer) at age 40 or younger",
    "one first degree relative with a history of Two or more different Primary Solid Tumors (excluding basal or squamous cell skin cancer)",
    "one first degree relative with a history of Neuroendocrine tumor",
    "one second-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome",
    "one second-degree relative with a history of cancer associated with Lynch Syndrome diagnosed at age 50 or younger",
    "Epithelial ovarian, fallopian tube, or primary peritoneal cancer in at least 1 close blood relative at any age",
    "Male close blood relative with breast cancer",
    "Metastatic (radiographic evidence of or biopsy proven disease) or intraductal/cribriform histology, high- or very-high risk prostate cancer in at least 1 close blood relative at any age",
    "First-degree or Seconde-degree relative with a history of Two or more Cancers Associated with Lynch Syndrome"]             

    if genetic_tests in ["WES", "WGS"]:
        q5 = "Yes" if family_history in wes_wgs_family_history else "No"
    elif genetic_tests == "BRCA1/2":
        q5 = "Yes" if family_history in brca_family_history else "No"

    # q6 - counselor
    if insurance == "BCBS_FEP" and genetic_tests in ["BRCA1/2", "WES", "WGS"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"
    elif insurance == "Cigna" and genetic_tests in ["BRCA1/2", "CMA_developmental_disorder"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"

    cpt_mapping = {
    "WES": "81415",
    "WGS": "81425", 
    "BRCA1/2": "81162",
    "CMA": "81228",
    "CMA_developmental_disorder": "81228",
    "CMA_tumor": "81277"
}

    # q7 - cpt code
    if insurance in ["UHC", "Cigna"]:
        expected_cpt = cpt_mapping.get(genetic_tests)
        q7 = "Yes" if cpt_code == expected_cpt else "No"

    # q8 - final decision
    all_answers = [q1, q2, q3, q4, q5, q6, q7]   
    if "No" in all_answers:
        q8 = "No"
    else:
        q8 = "Yes"           
                
    return {
        'Q0': q0,
        'Q1': q1,  
        'Q2': q2,  
        'Q3': q3,  
        'Q4': q4,  
        'Q5': q5,  
        'Q6': q6,  
        'Q7': q7,  
        'Q8': q8
    } 
    

def make_it_real_llm(sample_patient_dict):
    # Simulate a free-text for a sample patient
    patient_without_cpt = {k: v for k, v in sample_patient_dict.items() if k != 'cpt_code'}
    Instruction = "Generate a free-text description for the following sample patient. Add necessary detailes"
    # Using ChatGPT-like model to generate a free-text description
    prompt = f"{Instruction}: {patient_without_cpt}"
    # Here we would call the LLM API to get the response, but for this example
    model = 'gpt-3.5-turbo'
    # call openai api to get the response
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    patient_description = response.choices[0].message['content']
    return f"Sample Patient: {patient_description}"

def is_this_like_a_real_patient(sample_patient_dict):
    # Simulate a check to see if the sample patient is like a real patient
    Instruction = "Read the following sample patient. Determine if this is like a real patient. If yes, return 'True', otherwise return 'False'."
    # Using ChatGPT-like model to generate a free-text description
    prompt = f"{Instruction}: {sample_patient_dict}"
    # Here we would call the LLM API to get the response, but for this example
    model = 'gpt-3.5-turbo'
    # call openai api to get the response
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    is_true = response.choices[0].message['content']
    is_true = is_true.strip().lower() == 'true'  # Normalize the response to boolean
    return is_true

number_of_samples = 100  # Number of sample patients to generate
idx = 0
while idx < number_of_samples:
    insurance = random.choice(insurance_options)
    sample_patient = {
        "insurance": insurance,
        "genetic_tests": random.choice(genetic_tests_options[insurance]),
        "age": generate_age_in_category(),
        "order_provider": random.choice(order_providers_options),
        "clinical_indication": random.choice(clinical_indications_options),
        "prior_testing": random.choice(prior_testing_options),  
        "family_history": random.choice(family_history_options),
        "genetic_counselor": random.choice(genetic_counselor_options),
        "cpt_code": random.choice(cpt_codes_options)
    }

    if is_this_like_a_real_patient(sample_patient):
        sample_patient_text = make_it_real_llm(sample_patient)
        answer = get_answers(sample_patient)
        # create a big json file for each sample patient
        sample_patient_dict = {
            'sample_patient': sample_patient,
            'sample_patient_text': sample_patient_text,
            'answers': answer
        }
        # Save the sample patient dict to a json file
        import os
        dataset_dir = '/home/cptaswadu/RESCUE-n8n/insurance/dataset/qa_sample_patients'
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
        with open(f'{dataset_dir}/sample_patient_{idx}.json', 'w') as f:
            json.dump(sample_patient_dict, f, indent=4)
        idx += 1
