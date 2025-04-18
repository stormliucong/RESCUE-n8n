"""
Evaluation Prompt:
Submit a waiver form and a consent form for Patient ID PAT001, including references to the appropriate documents and policies:
- Name: John Doe
- DOB: 1990-06-15
- Patient id: PAT001
- creation date: 2024-12-24T09:35:00+11:00
The url of the document insurance waiver is http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510
"""
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_organization, create_practitioner

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
practitioner = create_practitioner()
upsert_to_fhir(practitioner)



document_data = {
  "resourceType" : "DocumentReference",
  "id" : "DOC001",
  "contained" : [{
    "resourceType" : "Patient",
    "id" : "PAT001",
    "name" : [{
      "family" : "Doe",
      "given" : ["John"]
    }]
  }],
  "status" : "current",
  "docStatus" : "preliminary",
  "type" : {
    "text" : "Insurance Waiver",
  },
  "subject" : {
    "reference" : "Patient/PAT001"
  },
  "date" : "2024-12-24T09:35:00+11:00",
  "author" : [{
    "reference" : "Practitioner/PRACT001" # who should be the author?
  }],
  "description" : "Waiver form",
  "content" : [{
    "attachment" : {
      "contentType" : "application/hl7-v3+xml",
      "language" : "en-US",
      "url" : "http://example.org/xds/mhd/Binary/07a6483f-732b-461e-86b6-edb665c45510",
      "title" : "Insurance Waiver",
      "creation" : "2024-12-24T09:35:00+11:00"
    }
  }]
}



response = requests.post(f"{FHIR_SERVER_URL}/DocumentReference", headers=HEADERS, json=document_data)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)

document_id = response_data["id"]

consent_data={
  "resourceType" : "Consent",
  "status" : "active",
  "subject" : {
    "reference" : "Patient/PAT001",
  },
  "date" : "2025-03-24",
  "controller" : [{
    "reference" : "Organization/ORG001"
  }],
  "sourceAttachment" : [{
    "title" : "The terms of the consent."
  }],
  "policyText": {
  "reference": f"DocumentReference/{document_id}"} #TODO: failed to add policy text
}

response = requests.post(f"{FHIR_SERVER_URL}/Consent", headers=HEADERS, json=consent_data)
# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)