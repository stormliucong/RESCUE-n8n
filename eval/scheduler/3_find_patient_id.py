"""
Evaluation Prompt:
3.
Search the database for the following patient: Name: John Doe.  DOB: 1990-06-15. 
If the patient does exits, return the Patient resource ID.
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

# Expected actions for agent
search_params = {
    "family": "Doe",
    "given": "John",
    "birthdate": "1990-06-15"
}
search_response = requests.get(f"{FHIR_SERVER_URL}/Patient", headers=HEADERS, params=search_params)

# Verify the response status code
assert search_response.status_code == 200, f"Expected status code 200, but got {search_response.status_code}. Response body: {search_response.text}"
assert 'total' in search_response.json(), "Expected to find total in the response"
assert search_response.json()['total'] > 0, "Expected to find at least one patient"
assert 'entry' in search_response.json(), "Expected to find entry in the response"
assert len(search_response.json()['entry']) > 0, "Expected to find at least one patient"
assert 'id' in search_response.json()['entry'][0]['resource'], "Expected to find id in the response"
assert search_response.json()['entry'][0]['resource']['id'] == 'PAT001', "Expected to find patient id PAT001"





