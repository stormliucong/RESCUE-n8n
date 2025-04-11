"""
Evaluation Prompt:
19.
Patient needs a urgent visit before April 25. Find an available slot for him.
20.
Patient needs a general visit on next Friday. Find an available slot for him.
21.
Patient needs a urgent visit before tomorrow. Find an available slot for him, if not, try to see whether other booked appointments and be rescheduled.
TODO: finish 19 and 21 test scripts
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



params = {
    "start": "le2025-04-25T23:59:59Z",
    "status": "free"}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)

