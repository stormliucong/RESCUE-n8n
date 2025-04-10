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



appointment_data = {
    "resourceType": "Appointment",
    "status": "cancelled"
}


appointment_id = "APPT001"
response = requests.put(f"{FHIR_SERVER_URL}/Appointment/{appointment_id}", json=appointment_data)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)

# update slot status


slot_id = response.json()["slot"][0].split("/")[-1]

slot_data = {
    "resourceType": "Slot",
    "id": slot_id,
    "status": "free"
}

response = requests.put(f"{FHIR_SERVER_URL}/Slot", json=slot_data)
# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)
