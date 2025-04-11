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
waitlist = create_appointment(
    patient_id=patient["id"], practitioner_id=practitioner["id"], waitlist= True
)
upsert_to_fhir(waitlist)


appointment_id = "APPT001"

# Retrieve the existing Appointment resource
response = requests.get(f"{FHIR_SERVER_URL}/Appointment/{appointment_id}")
if response.status_code == 200:
    appointment_data = response.json()
    # Modify the status field
    appointment_data["status"] = "booked"
    # Update the resource on the server
    update_response = requests.put(
        f"{FHIR_SERVER_URL}/Appointment/{appointment_id}",
        json=appointment_data,
        headers={"Content-Type": "application/fhir+json"},
    )
    if update_response.status_code == 200:
        print("Appointment updated successfully.")
        print(update_response.json())
    else:
        print(
            f"Failed to update appointment: {update_response.status_code} {update_response.text}"
        )
else:
    print(f"Failed to retrieve appointment: {response.status_code} {response.text}")

# update slot status as busy
slot_id = update_response.json()["slot"][0]["reference"].split("/")[-1]

response = requests.get(f"{FHIR_SERVER_URL}/Slot/{slot_id}", headers=HEADERS)

assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
slot_data = response.json()
slot_data["status"] = "busy"

update_response = requests.put(
    f"{FHIR_SERVER_URL}/Slot/{slot_id}", headers=HEADERS, json=slot_data
)

assert (
    update_response.status_code == 200
), f"Expected status code 200, but got {update_response.status_code}. Response body: {update_response.text}"
# inspect the response content
response_data = update_response.json()
print("Slot updated successfully. Response:")
print(response_data)
