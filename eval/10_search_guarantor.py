"""
Evaluation Prompt:
Identify and confirm the guarantor responsible for this patient's insurance policy.
 Patient's details:
 - Name: John Doe, patient id = 001
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
patient = create_patient()
upsert_to_fhir(patient)
related_person = create_related_person(patient_id=patient["id"])
upsert_to_fhir(related_person)
account = create_account(patient_id=patient["id"])
upsert_to_fhir(account)  



# Find if guarantor exists 
params = {
  "patient" : "Patient/PAT001",
}
response = requests.get(f"{FHIR_SERVER_URL}/Account", headers=HEADERS, params=params)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Guarantor found successfully. Response:")
print(response_data)


# get guarantor info
params = {
  "patient" : "Patient/PAT001",
}

response = requests.get(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Related Person found successfully. Response:")
print(response_data)




# Empty cases
params = {
  "patient" : "Patient/PAT002",
}

response = requests.get(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, params=params)

# verify if the response is empty
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert (
    not response_data.get("entry")
), f"Expected no guarantors, but found: {response_data.get('entry')}"
print("No guarantors found for the given patient.")
