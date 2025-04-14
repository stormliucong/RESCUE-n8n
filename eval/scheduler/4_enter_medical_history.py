"""
Evaluation Prompt:
Record a medical condition for the patient id=PAT001 in his medical history that he has a hypertension. 
Using SNOMED CT (http://snomed.info/sct) for coding.
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

delete_all_resources()  # Clean up existing resources before the test
# Create a patient
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

# Expected actions for agent
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


response = requests.post(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, json=condition_data)
# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
