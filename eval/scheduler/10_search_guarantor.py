"""
Evaluation Prompt:
10a.
Identify and confirm the guarantor responsible for this patient's insurance policy.
 Patient's details:
 - Name: John Doe, PAT001
 
 Identify and confirm the guarantor responsible for this patient's insurance policy.
 Patient's details:
 - Name: John Doe, PAT002
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_related_person, create_account
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
related_person_resource = {
    "resourceType": "RelatedPerson",
    "id": "REL001",
    "patient": {"reference": "Patient/PAT001"},
    "relationship": [{"text": "mother"}],
    "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
    "gender": "female",
    "birthDate": "1960-03-01",
}
related_person = create_related_person(related_person_resource)
upsert_to_fhir(related_person)
account_resource = {
    "resourceType": "Account",
    "id": "ACC001",
    "status": "active",
    "subject": {"reference": "Patient/PAT001"},
    "guarantor": [{"party": {"reference": "RelatedPerson/REL001"}}],
}
account = create_account(account_resource)
upsert_to_fhir(account)
patient_resource = {
    "resourceType": "Patient",
    "id": "PAT002",
    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
    "birthDate": "2020-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient) 
# Expected actions for agent
# 10a. 
params = {
  "patient" : "Patient/PAT001",
}
response = requests.get(f"{FHIR_SERVER_URL}/Account", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one guarantor, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one guarantor, but got {len(response.json()['entry'])}"

# Optionally, inspect the response content
response_data = response.json()
print("Guarantor found successfully. Response:")
print(response_data['entry'][0]['resource']['guarantor'][0]['party']['reference'])


# 10b.
params = {
  "patient" : "Patient/PAT002",
}
response = requests.get(f"{FHIR_SERVER_URL}/Account", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] == 0, f"Expected to find no guarantor, but got {response.json()['total']}"
