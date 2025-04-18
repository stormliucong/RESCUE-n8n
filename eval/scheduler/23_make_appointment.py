"""
Evaluation Prompt:
Make an appointment time for the patient id =PAT001 and slot id = 1 , practitioner id PRAC001, on April 25th 9:15-9:30 am.
"""
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
slot_id = "SLOT001"
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
    "slot": [{"reference": f"Slot/{slot_id}"}],
}

response = requests.post(
    f"{FHIR_SERVER_URL}/Appointment", 
    headers=HEADERS,
    json=appointment_data
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
response = requests.get(f"{FHIR_SERVER_URL}/Slot/{slot_id}", headers=HEADERS)

if response.status_code == 200:
    slot_data = response.json()
    slot_data["status"] = "free"

update_response = requests.put(
    f"{FHIR_SERVER_URL}/Slot/{slot_id}",
    headers=HEADERS,
    json=slot_data
)

assert (
    update_response.status_code == 200
), f"Expected status code 200, but got {update_response.status_code}. Response body: {update_response.text}"
# inspect the response content
response_data = update_response.json()
print("Slot updated successfully. Response:")
print(response_data)