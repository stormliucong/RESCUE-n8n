
import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources, create_related_person
FHIR_SERVER_URL = "http://165.22.13.117:7070/fhir"

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

delete_all_resources()  # Clean up existing resources before the test
patient = create_patient()
upsert_to_fhir(patient)
related_person = create_related_person(patient_id=patient["id"])
upsert_to_fhir(related_person)


params = {
  "patient" : "Patient/PAT001",
}

response = requests.get(f"{FHIR_SERVER_URL}/RelatedPerson", headers=HEADERS, params=params)

# Verify the response status code
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)
