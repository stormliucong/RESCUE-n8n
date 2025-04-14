"""
Evaluation Prompt:
Search for the existing patient id=PAT001 to see if he has any medical history.
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
patient = create_patient()
upsert_to_fhir(patient)
condition = create_condition(patient_id=patient["id"])
upsert_to_fhir(condition)


params = {
    "subject" : "Patient/PAT001"
}

response = requests.get(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)



# Empty cases
params = {
    "subject" : "Patient/PAT002"
}

response = requests.get(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, params=params)

# verify if the response is empty
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert (
    not response_data.get("entry")
), f"Expected no medical history, but found: {response_data.get('entry')}"
print("No medical history found for the given patient.")


