import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources

FHIR_SERVER_URL = "http://165.22.13.117:7070/fhir"

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

# delete_all_resources()  # Clean up existing resources before the test
# patient = create_patient()
# upsert_to_fhir(patient)

condition_data = {
  "resourceType" : "Condition",
    "code": {
       "text": "Hypertension"
    },
  "subject" : {
    "reference" : "Patient/PAT001"
  },
  "clinicalStatus": {"text": "active"}
}


response = requests.post(f"{FHIR_SERVER_URL}/Condition", headers=HEADERS, json=condition_data)

# Verify the response status code
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)
