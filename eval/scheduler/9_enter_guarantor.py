"""
Evaluation Prompt:
9a.
Create a related person resource for the patient PAT001 if not already present

9b. Create an account resource for the patient PAT001 if not already present

9c.
Add the guarantor responsible for this patient's billing.
 Patient's details:
 - Guarantor: Alice Doe 
 - Relationship: Mother
 - Guarantor DOB: 1960-03-01
"""
import requests
from generate_schedule_sync_data import (
    create_patient,
    upsert_to_fhir,
    delete_all_resources
)

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

delete_all_resources()  # Clean up existing resources before the test
patient_resource = {
    "resourceType": "Patient",
    "id": "PAT001",
    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
    "birthDate": "2010-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)

# 9a.
data = {
    "resourceType": "RelatedPerson",
    "patient": {"reference": "Patient/PAT001"},
    "relationship": [{"text": "mother"}],
    "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
    "gender": "female",
    "birthDate": "1960-03-01",
}
response = requests.post(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, json=data)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"


# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)

# 9b.
data = {
    "resourceType": "Account",
    "id": "ACC001",
    "status": "active",
    "subject": {"reference": f"Patient/PAT001"}
}
response = requests.post(f"{FHIR_SERVER_URL}/Account", headers=HEADERS, json=data)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)

# 9c.
data = {
    "resourceType": "Account",
    "id": "ACC001",
    "guarantor": [{"party": {"reference": f"RelatedPerson/REL001"}}],
}

response = requests.put(f"{FHIR_SERVER_URL}/Account/ACC001", headers=HEADERS, json=data)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
assert response.json()['guarantor'][0]['party']['reference'] == 'RelatedPerson/REL001', f"Expected guarantor reference to be REL001, but got {response.json()['guarantor'][0]['party']['reference']}"

# Optionally, inspect the response content
response_data = response.json()
print("Account resource updated successfully. Response:")
print(response_data)
