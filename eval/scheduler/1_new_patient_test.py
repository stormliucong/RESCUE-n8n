"""
Evaluation Prompt:
A new patient needs to be registered. Please enter the following details into the system:
 - Name: John Doe
 - Date of Birth: 1990-06-15
 - Phone: (123) 456-7890
 - Address: 123 Main St, Boston, MA
"""
import requests

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
from generate_schedule_sync_data import delete_all_resources



HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

# Expected actions for agent
payload = {
    "resourceType": "Patient",
    "name": [
        {
            "use": "official",
            "family": "Doe",
            "given": ["John"]
        }
    ],
    "birthDate": "1990-06-15",
    "telecom": [
        {
            "system": "phone",
            "value": "(123) 456-7890"
        }
    ],
    "address": [
        {
            "line": ["123 Main St"],
            "city": "Boston",
            "state": "MA"
        }
    ]
}
delete_all_resources()  # Clean up existing resources before the test

response = requests.post(f"{FHIR_SERVER_URL}/Patient", headers=HEADERS, json=payload)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
