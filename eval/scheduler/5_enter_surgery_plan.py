"""
Evaluation Prompt:
5.
Record a surgery plan for patient id =PAT001 for a Appendectomy surgery planned for 2025-05-01.
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

# 5. Expected actions for agent
service_request = {
  "resourceType": "ServiceRequest",
  "status": "active",
  "intent": "order",
  "code": {
    "concept": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "80146002",
        "display": "Appendectomy (procedure)"
      }],
      "text": "Appendectomy"
    }
  },
  "subject": {
    "reference": f"Patient/PAT001"
  },
  "occurrenceDateTime": "2025-05-01"
}

response = requests.post(f"{FHIR_SERVER_URL}/ServiceRequest", headers=HEADERS, json=service_request)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
