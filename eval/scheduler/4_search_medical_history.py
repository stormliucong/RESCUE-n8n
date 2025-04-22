"""
Evaluation Prompt:
4a. 
Search for the existing patient id=PAT001 to see if he has any medical history.

4b.
Search for the existing patient id=PAT002 to see if he has any medical history.
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_condition

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
    "birthDate": "1990-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)
condition_data = {
  "resourceType": "Condition",
  "id": "Appendicitis001",
  "subject": { "reference": "Patient/PAT001" },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "74400008",
      "display": "Appendicitis"
    }],
    "text": "Appendicitis"
  },
  "clinicalStatus": { "coding": [{ "code": "active" }] }
}
condition = create_condition(condition_resource=condition_data)
upsert_to_fhir(condition)
patient_resource = {
    "resourceType": "Patient",
    "id": "PAT002",
    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
    "birthDate": "1990-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)

# 4a. Expected actions for agent
params = {
    "subject" : "Patient/PAT001"
}

response = requests.get(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, params=params)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one medical history, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one medical history, but got {len(response.json()['entry'])}"

# 4b. Expected actions for agent
params = {                      
    "subject" : "Patient/PAT002"
}

response = requests.get(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] == 0, f"Expected no medical history, but got {response.json()['total']}"
assert 'entry' not in response.json(), f"Expected no entries in the response"


