"""
Evaluation Prompt
7a.
Search and find if patient id =PAT001 has any surgery plan two weeks from now.

7b.
Search and find if patient id =PAT002 has any surgery plan two weeks from now.
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_service_request

import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

today = datetime.today().date()
two_weeks_later = today + timedelta(days=14)
one_week_later = today + timedelta(days=7)
three_weeks_later = today + timedelta(days=21)


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
service_request = {
  "resourceType": "ServiceRequest",
  "id": "APPENDECTOMY-REQUEST-001",
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
  "occurrenceDateTime": one_week_later.strftime("%Y-%m-%d")
}
service_request = create_service_request(service_request_resource=service_request)
upsert_to_fhir(service_request)
patient_resource = {
    "resourceType": "Patient",
    "id": "PAT002",
    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
    "birthDate": "1991-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)
service_request = {
  "resourceType": "ServiceRequest",
  "id": "APPENDECTOMY-REQUEST-002",
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
    "reference": f"Patient/PAT002"
  },
  "occurrenceDateTime": three_weeks_later.strftime("%Y-%m-%d")
}

# 7a. Expected actions for agent

params = {
    "subject": "Patient/PAT001",  # Replace with the actual Patient ID
    "occurrence": [
        f"ge{today.isoformat()}",
        f"le{two_weeks_later.isoformat()}"
    ]
}
response = requests.get(f"{FHIR_SERVER_URL}/ServiceRequest", headers=HEADERS, params=params)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one medical history, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one medical history, but got {len(response.json()['entry'])}"
# Optionally, inspect the service request
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)

# 7b. Expected actions for agent
params = {
    "subject": "Patient/PAT002",  # Replace with the actual Patient ID
    "occurrence": [
        f"ge{today.isoformat()}",
        f"le{two_weeks_later.isoformat()}"
    ]
}
response = requests.get(f"{FHIR_SERVER_URL}/ServiceRequest", headers=HEADERS, params=params)
# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] == 0, f"Expected no medical history, but got {response.json()['total']}"
assert 'entry' not in response.json(), f"Expected no entries in the response"


