"""
Evaluation Prompt:
7a.
Create a related person resource for the patient PAT001 if not already present

7b.
The patient PAT001 has a Acme Health Insurance policy. Please find the organization resource for Acme Health Insurance.

7c.
Add the following insurance details for the patient PAT001.
The insurance is provided by Acme Health Insurance (ORG-INSURER001)
The policy is active from January 1, 2024 to December 31, 2025.
The subscriber and policy holder is the patient father.
Group Plan: Employer Group Plan (Group ID: Group-98765)
Plan ID: GOLD123 
"""

import requests
from generate_schedule_sync_data import create_patient, create_related_person, upsert_to_fhir, delete_all_resources, create_organization

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

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
organization_resource = {
    "resourceType": "Organization",
    "id": "ORG-INSURER001",
    "name": "Acme Health Insurance"
}
organization = create_organization(organization_resource)
upsert_to_fhir(organization)

# Optionally: create a related person resource for the patient father
# related_person_resource = {
#     "resourceType": "RelatedPerson",
#     "id": "PAT001-FATHER",
#     "patient": "Patient/PAT001",
# }
# related_person = create_related_person(related_person_resource)
# upsert_to_fhir(related_person)  

# Expected actions for agent
# 7a.
payload = {
    "resourceType": "RelatedPerson",
    "patient": "Patient/PAT001",
    "relationship": [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v3-RoleCode', 'code': 'FATHER'}]}],
}
response = requests.post(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, json=payload)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)

father_id = response_data['id']

# 7b.
# FHIR does not support fuzzy matching, so we need to find the exact match
params = {"name":"Acme Health Insurance"}
response = requests.get(f"{FHIR_SERVER_URL}/Organization", headers=HEADERS, params=params)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] >= 1, f"Expected 1 insurance, but got {response.json()['total']}"   
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) >= 1, f"Expected 1 insurance, but got {len(response.json()['entry'])}"

# 7c.
payload = { 'resourceType': 'Coverage', 
'status': 'active', 
'kind': {'coding': [{'system': 'http://hl7.org/fhir/coverage-kind', 'code': 'insurance'}]},
'subscriber': {'reference': f'RelatedPerson/{father_id}'},
'beneficiary': {'reference': 'Patient/PAT001'},
'insurer': {'reference': 'Organization/ORG-INSURER001'},
'period': {'start': '2024-01-01', 'end': '2025-12-31'},
'class': [{'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'group'}]}, 'value': 'Group-98765'}, {'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'plan'}]}, 'value': 'Plan-GOLD123'}],
}
response = requests.post(f"{FHIR_SERVER_URL}/Coverage", headers=HEADERS, json=payload)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
