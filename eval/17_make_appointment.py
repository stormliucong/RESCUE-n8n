import requests
from generate_schedule_sync_data import (
    create_patient,
    upsert_to_fhir,
    delete_all_resources,
    create_practitioner,
    create_schedule,
    create_location,
    create_free_slot,
    create_busy_slot,
)


import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

delete_all_resources()  # Clean up existing resources before the test
patient = create_patient()
upsert_to_fhir(patient)
practitioner = create_practitioner()
upsert_to_fhir(practitioner)
location = create_location()
upsert_to_fhir(location)
schedule = create_schedule()
upsert_to_fhir(schedule)
slot = create_free_slot()
upsert_to_fhir(slot)
slot = create_busy_slot()
upsert_to_fhir(slot)

patient_id = "PAT001"
practitioner_id = "PRACT001"
# Create a new appointment resource
appointment_data = {
    "resourceType": "Appointment",
    "status": "booked",
    "start": "2025-04-25T09:15:00Z",
    "end": "2025-04-25T09:30:00Z",
    "participant": [
        {"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"},
        {
            "actor": {"reference": f"Practitioner/{practitioner_id}"},
            "status": "accepted",
        },
        {"actor": {"location": {"reference": "Location/LOC001"}}},
    ],
    "slot": [{"reference": "Slot/SLOT001"}],
}

response = requests.post(
    f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, json=appointment_data
)

# Verify the response status code
assert (
    response.status_code == 201
), f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource created successfully. Response:")
print(response_data)

# update the slot as busy
slot_data = {"resourceType": "Slot", "status": "busy", "id": "SLOT001"}
response = requests.put(f"{FHIR_SERVER_URL}/Slot", json=slot_data)
# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Slot updated successfully. Response:")
print(response_data)
