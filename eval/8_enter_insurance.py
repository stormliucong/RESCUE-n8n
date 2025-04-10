import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_organization

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


data = { 'resourceType': 'Coverage', 
'status': 'active', 
'kind': 'insurance', # TODO: failed to add kind
 "subscriber" : {
    "reference" : "Patient/PAT001"
  },
 "beneficiary" : {
    "reference" : "Patient/PAT001"
  },
  "insurer" : {
    "reference" : "Organization/ORG001"
  },
  "period" : {
    "start" : "2024-05-23",
    "end" : "2025-05-23"
  }
}


response = requests.post(f"{FHIR_SERVER_URL}/Coverage", headers=HEADERS, json=data)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
