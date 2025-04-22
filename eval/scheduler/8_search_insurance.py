"""
Evaluation Prompt:

8.
Search if patient insurance information has been entered in the system
 - beneficiary: John Doe (id=PAT001)
"""
import requests
from generate_schedule_sync_data import create_organization, create_patient, create_related_person, upsert_to_fhir, delete_all_resources, create_coverage
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
    "birthDate": "2010-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)
patient_resource = {
    "resourceType": "Patient",
    "id": "PAT002",
    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
    "birthDate": "2020-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
patient = create_patient(patient_resource)
upsert_to_fhir(patient)
organization_resource = {
    "resourceType": "Organization",
    "id": "ORG-INSURER001",
    "name": "Acme Health Insurance"
}
organization = create_organization(organization_resource)
upsert_to_fhir(organization)
related_person_resource = {
    "resourceType": "RelatedPerson",
    "id": "PAT001-FATHER",
    "patient": "Patient/PAT001",
}
related_person = create_related_person(related_person_resource)
upsert_to_fhir(related_person)
coverage_resource = { 
  'resourceType': 'Coverage', 
  'id': 'COV-PAT001',
  'status': 'active', 
  'kind': {'coding': [{'system': 'http://hl7.org/fhir/coverage-kind', 'code': 'insurance'}]},
  'subscriber': {'reference': f'RelatedPerson/PAT001-FATHER'},
  'beneficiary': {'reference': 'Patient/PAT001'},
  'insurer': {'reference': 'Organization/ORG-INSURER001'},
  'period': {'start': '2024-01-01', 'end': '2025-12-31'},
  'class': [{'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'group'}]}, 'value': 'Group-98765'}, {'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'plan'}]}, 'value': 'Plan-GOLD123'}],
}
coverage = create_coverage(coverage_resource)
upsert_to_fhir(coverage)


# Expected actions for agent
# 8a.
params = {
  "beneficiary" : "Patient/PAT001",
  'status': 'active'
}

response = requests.get(f"{FHIR_SERVER_URL}/Coverage", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] >= 1, f"Expected 1 insurance, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) >= 1, f"Expected 1 insurance, but got {len(response.json()['entry'])}"




# 8b.
params = {
  "beneficiary" : "Patient/PAT002",
  'status': 'active'
}

response = requests.get(f"{FHIR_SERVER_URL}/Coverage", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] == 0, f"Expected no medical history, but got {response.json()['total']}"
assert 'entry' not in response.json(), f"Expected no entries in the response"

