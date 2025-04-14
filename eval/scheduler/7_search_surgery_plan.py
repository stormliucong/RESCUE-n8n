"""
Evaluation Prompt
Search and find if patient id =PAT001 has any surgery plan in progress.
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_procedure

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

delete_all_resources()  # Clean up existing resources before the test
patient = create_patient()
upsert_to_fhir(patient)
procedure = create_procedure(patient_id=patient["id"])
upsert_to_fhir(procedure)

params = {
    "subject" : "Patient/PAT001"
}

response = requests.get(f"{FHIR_SERVER_URL}/Procedure", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)


# Empty cases
params = {
    "subject" : "Patient/PAT001"
}

response = requests.get(f"{FHIR_SERVER_URL}/Procedure", headers=HEADERS, params=params)

# verify if the response is empty
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert (
    not response_data.get("entry")
), f"Expected no care plan, but found: {response_data.get('entry')}"
print("No care plan found for the given patient.")


