import requests
from generate_schedule_sync_data import create_patient, upsert_to_fhir, delete_all_resources

FHIR_SERVER_URL = "http://165.22.13.117:7070/fhir"

HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

delete_all_resources()  # Clean up existing resources before the test
patient = create_patient()
upsert_to_fhir(patient)

search_params = {
    "family": "Doe",
    "given": "John",
    "birthdate": "1990-06-15"
}
search_response = requests.get(f"{FHIR_SERVER_URL}/Patient", headers=HEADERS, params=search_params)

# Verify the response status code
assert search_response.status_code == 200, f"Expected status code 200, but got {search_response.status_code}. Response body: {search_response.text}"

# Optionally, inspect the response content
response_data = search_response.json()
print("Resource created successfully. Response:")
print(response_data)
