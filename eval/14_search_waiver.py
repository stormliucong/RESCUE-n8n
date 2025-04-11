
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_organization, create_document_reference, create_consent
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
organization = create_organization()
upsert_to_fhir(organization)
document_reference = create_document_reference(patient_id=patient["id"])
upsert_to_fhir(document_reference)
consent = create_consent(patient_id=patient["id"])
upsert_to_fhir(consent)


params = {
  "patient" : "Patient/PAT001"
}

response = requests.get(f"{FHIR_SERVER_URL}/Consent", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)

if "entry" not in response_data or len(response_data["entry"]) == 0:
    raise ValueError("No entries found in the response data.")

# Extract the first entry's resource ID
document_reference_id = response_data["entry"][0]["resource"]["policyText"]

response = requests.get(f"{FHIR_SERVER_URL}/DocumentReference/{document_reference_id}", headers=HEADERS)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)