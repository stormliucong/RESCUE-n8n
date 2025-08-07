# import library
import random
import json
from collections import defaultdict
# import openai
import pandas as pd
import numpy as np
import os
# setup OpenAI API key by loading .env file
# from dotenv import load_dotenv
# load_dotenv()

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
order_providers_options = ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician", "Primary Care Physician", "General Pediatrician", "Nurse Practitioner"]

# q3 - clinical indications
# category to clinical indications mapping
q3_cat_ind = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_ind_q3.csv')
# category to insurance coverage (test - insurance company) mapping
q3_cat_test_ins = pd.read_csv('/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset/cat_test_ins_q3.csv')
# merge two dataframes on 'Category' column: category, Indications, insurance coverage
q3_merged = pd.merge(q3_cat_ind, q3_cat_test_ins, on='Category', how='outer', suffixes=('_ins', '_ind'))

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
genetic_counselor_options = ["Saw a genetic counselor before testing and will visit after results are received", "No genetic counseling conducted", "No mention of genetic counseling"]

# q7 - CPT codes
cpt_codes_options = ["81162", "81277", "81228", "81415", "81425", "Not specified"]

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
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"

    if insurance == "UHC":
        if genetic_tests == "WES": # prenatal case included
            if is_in_age_range(age, [(-1,0), (0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  # 0-17, 66-75
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  # 18-65
                q1 = "Yes"

        elif genetic_tests == "WGS": # prenatal case not included
            if is_in_age_range(age, [(0,0), (0,18)]):
                q1 = "Yes"
            else:
                q1 = "No"

    if insurance == "Cigna":
        if genetic_tests == "WES": # prenatal case included
            if is_in_age_range(age, [(-1,0), (0,0), (0,21)]):
                q1 = "Yes"
            else:
                q1 = "No"

        elif genetic_tests == "BRCA1/2":
            if is_in_age_range(age, [(-1,0), (0,0), (0,17), (66,75)]):  
                q1 = "No"
            elif is_in_age_range(age, [(18,45), (46,65)]):  
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

        # no age criteria for CMA_tumor

    # q2 - order provider (only UHC WES/WGS has specific criteria)
    if insurance == "UHC":
        if genetic_tests in ["WES", "WGS"]:
            q2 = "Yes" if order_provider in ["Oncologist", "Neurologist", "Medical Geneticist", "Neonatologist", "Developmental Pediatrician"] else "No"    
    
    # q3 - clinical indication
    # filter test first, if not exist, return "No"
    test_info = q3_merged[q3_merged['Test'] == genetic_tests]
    if test_info.empty:
        q3 = "No"
    else:
        # check if clinical indication exists for the test
        indication_data = test_info[test_info['Indication'] == clinical_indication]
        if indication_data.empty:
            q3 = "No"
        else:
            # check if insurance coverage exists for the test and clinical indication
            coverage = indication_data[indication_data['Insurance'] == insurance]
            if coverage.empty:
                q3 = "No"
            else:
                q3 = "Yes"

    # q4 - Prior Testing (For WES/WGS/CMA_developmental_disorder only)
    if genetic_tests in ["WES", "WGS"]:
        q4 = "Yes" if prior_testing in ["CMA", "Fragile X testing", "FISH testing", "Karyotype testing"] else "No"
    if insurance == "Cigna" and genetic_tests == "CMA_developmental_disorder":
        q4 = "Yes" if prior_testing in ["FISH testing", "Karyotype testing"] else "No"

    # q5 - family history
    test_info = q5_merged[q5_merged['Test'] == genetic_tests]

    if test_info.empty:
        q5 = "Not specified"  # Test itself does not exist in family history policy
    else:
        # Check if family_history is included in the test
        history_data = test_info[test_info['Family history'] == family_history]
    
        if history_data.empty:
            q5 = "Not specified"  # This family history is not mentioned in policy
        else:
            # Check insurance coverage
            coverage_data = history_data[history_data['Insurance'] == insurance]

            if coverage_data.empty:
                q5 = "Not specified"  # Insurance doesn't have policy for this family history
            else:
                # Insurance has specific policy for this family history
                q5 = "Yes"  # Coverage confirmed

    # q6 - counselor (For BCBS_FEP BRCA1/2, WES, WGS; Cigna BRCA1/2, CMA_developmental_disorder only)
    if insurance == "BCBS_FEP" and genetic_tests in ["BRCA1/2", "WES", "WGS"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"
    elif insurance == "Cigna" and genetic_tests in ["BRCA1/2", "CMA_developmental_disorder"]:
        q6 = "Yes" if genetic_counselor == "Saw a genetic counselor before testing and will visit after results are received" else "No"

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
                q7 = "Not specified"  # Cigna does not have CMA itself in the policy
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
        sample_patient.get("case_id"): {
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
    

def make_it_real_llm(sample_patient_dict):
    # Simulate a free-text for a sample patient
    patient_without_cpt = {k: v for k, v in sample_patient_dict.items() if k != 'cpt_code'} # exclude cpt code
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

number_of_samples = 1000  # Number of sample patients to generate
idx = 0 # initial index
samples = [] # empty list to store sample patients
# Generate sample patients
while idx < number_of_samples:
    case_id = f"Case{idx + 1}"  # starting form 1, make case_id
    age_years, age_string = generate_age_in_category(random.choice(age_categories))
    sample_patient = {
        "case_id": case_id,
        "insurance": random.choice(insurance_options),
        "genetic_tests": random.choice(test_options),
        "age_years": age_years,
        "age_string": age_string,
        "order_provider": random.choice(order_providers_options),
        "clinical_indication": random.choice(q3_merged['Indication']),
        "prior_testing": random.choice(prior_testing_options),  
        "family_history": random.choice(q5_merged['Family history']),
        "genetic_counselor": random.choice(genetic_counselor_options),
        "cpt_code": random.choice(cpt_codes_options)
    }
    
    answer = get_answers(sample_patient)
    samples.append(answer)
    idx += 1
    
def negative_sample_balanced_dataset(samples, target_size, test_proportions):  
    # considering the proportion of genetic tests & Q8 balance
    test_groups = defaultdict(list)  # initialize a dictionary to hold samples by test type
    for s in samples:
        case_data = list(s.values())[0] # get the first (and only) case data
        test_name = case_data["Q0"] # get the test name
        test_groups[test_name].append(s) # append the sample to the corresponding test group

    balanced_samples = [] # empty list to hold the balanced samples
    
    # Calculate Q8 ratio from entire dataset
    # count the number of "Yes" responses in Q8
    count_yes = sum(1 for s in samples for case_data in s.values() if case_data["Q8"] == "Yes")
    # calculate the ratio of "Yes" responses for q8
    p_q8_yes = count_yes / len(samples)
    
    def _compute_q8_weight(sample, p_q8_yes, epsilon=1e-6):
        # IPW
        case_data = list(sample.values())[0]
        if case_data["Q8"] == "Yes":
            return 1 / (p_q8_yes + epsilon)
        else:
            return 1 / (1 - p_q8_yes + epsilon)
    
    for test, proportion in test_proportions.items():
        group = test_groups.get(test, [])
        if not group:
            continue

        # Compute weights for each sample in the current group (fixed: was using entire samples)
        weights = [_compute_q8_weight(s, p_q8_yes) for s in group]
        # Normalize weights to sum to 1
        probabilities = np.array(weights) / np.sum(weights)
        k = int(target_size * proportion) # Calculate the number of samples to select for this test type
        selected = random.choices(group, weights=probabilities, k=k) # Select samples from the group
        balanced_samples.extend(selected) # extend the balanced samples with selected samples (not append, since we want to keep the structure of samples)
    
    return balanced_samples

test_ratios = {
    "WES": 0.3,
    "WGS": 0.2,
    "BRCA1/2": 0.3,
    "CMA": 0.2
}
balanced_samples = negative_sample_balanced_dataset(samples, target_size=100, test_proportions=test_ratios)


# Save the balanced samples to a JSON file
dataset_dir = '/home/cptaswadu/new-rescue/RESCUE-n8n/eval/insurance/dataset'
if not os.path.exists(dataset_dir):
    os.makedirs(dataset_dir)
with open(f'{dataset_dir}/balanced_samples.json', 'w') as f:
    json.dump(balanced_samples, f, indent=4)

# Check q8 balance
def print_q8_balance(dataset):
    total = len(dataset)
    yes = sum(1 for s in dataset for case_data in s.values() if case_data["Q8"] == "Yes")
    print(f"Q8 Yes: {yes/total:.2f}, No: {(total - yes)/total:.2f}")

print_q8_balance(balanced_samples)