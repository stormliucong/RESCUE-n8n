"""
Evaluation Prompt:
Add the guarantor responsible for this patient's insurance policy.
 Patient's details:
 - Name: John Doe (id=PAT001)
 - Guarantor: Alice Doe
 - Relationship: Mother
- DOB: 1960-03-01
"""
import requests
from generate_schedule_sync_data import (
    create_patient,
    upsert_to_fhir,
    delete_all_resources
)

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

delete_all_resources()  # Clean up existing resources before the test
patient = create_patient()
upsert_to_fhir(patient)


data = {
    "resourceType": "RelatedPerson",
    "patient": {"reference": "Patient/PAT001"},
    "relationship": [{"text": "mother"}],
    "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
    "gender": "female",
    "birthDate": "1960-03-01",
}


response = requests.post(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, json=data)

# Verify the response status code
assert (
    response.status_code == 201
), f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)


account_data = {
    "resourceType": "Account",
    "id": "ACC001",
    "status": "active",
    "type": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/account-type",
                "code": "guarantor",
                "display": "Guarantor",
            }
        ]
    },
    "name": "Guarantor Account",
    "subject": {"reference": f"Patient/PAT001"},
    "guarantor": [{"party": {"reference": f"RelatedPerson/REL001"}, "onHold": False}],
}


response = requests.post(
    f"{FHIR_SERVER_URL}/Account", headers=HEADERS, json=account_data
)


# Verify the response status code
assert (
    response.status_code == 201
), f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Account resource created successfully. Response:")
print(response_data)
