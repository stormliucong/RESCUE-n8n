"""
Evaluation Prompt:
Record a medical condition for the patient id=PAT001 in their medical history that he has a hypertension. 
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

# delete_all_resources()  # Clean up existing resources before the test
# patient = create_patient()
# upsert_to_fhir(patient)

condition_data = {
  "resourceType" : "Condition",
    "code": {
       "text": "Hypertension"
    },
  "subject" : {
    "reference" : "Patient/PAT001"
  },
  "clinicalStatus": {"text": "active"}
}


response = requests.post(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, json=condition_data)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
