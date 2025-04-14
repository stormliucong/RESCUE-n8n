"""
Evaluation Prompt:
19.
Patient needs a urgent visit before April 25. Find an available slot for him.
20.
Patient needs a general visit on next Friday. Find an available slot for him.
21.
Patient needs a urgent visit before tomorrow. Find an available slot for him, if not, try to see whether other booked appointments and be rescheduled.
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

# 19
params = {
    "start": "ge2025-04-25T00:00:00Z",
    "start": "le2025-04-25T23:59:59Z",
    "status": "free",
}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)


# 20
params = {
    "start": "ge2025-04-25T00:00:00Z",
    "start": "le2025-04-25T23:59:59Z",
    "status": "free",
}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)


# 21
print("action 21:")

params = {"start": "le2025-04-11T23:59:59Z", "status": "free"}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")


if not response_data.get("entry"):
    print(
        "No free slot available. Attempting to reschedule other booked appointments..."
    )

    # Fetch all busy slots to check for potential rescheduling
    params = {"status": "busy", "start": "le2025-04-11T23:59:59Z"}
    busy_slots_response = requests.get(
        f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params
    )

    # Verify the response status code
    assert (
        busy_slots_response.status_code == 200
    ), f"Expected status code 200, but got {busy_slots_response.status_code}. Response body: {busy_slots_response.text}"

    busy_slots_data = busy_slots_response.json()

    if busy_slots_data.get("entry"):
        print("Busy slots found. Attempting to reschedule...")
        for entry in busy_slots_data["entry"]:
            busy_slot = entry["resource"]
            # Logic to reschedule the busy slot (e.g., notify the patient, find alternative time)
            print(f"Found a busy slot: {busy_slot['id']}")
            break  # Stop after rescheduling one slot
    else:
        print("No busy slots available for rescheduling.")
else:
    print("Free slot found successfully. Response:")
    print(response_data)
