"""
Evaluation Prompt:
Get the patient John Doe id=PAT001's latest appointment
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
    create_appointment,
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
appointment = create_appointment(patient_id=patient["id"], practitioner_id=practitioner["id"])
upsert_to_fhir(appointment)


params = {
    "patient": "PAT001",
}

response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)



# Empty cases
params = {
    "patient": "PAT002",
}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
 
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert (
    not response_data.get("entry")
), f"Expected no appointments, but found: {response_data.get('entry')}"
print("No appointments found for the given patient.")