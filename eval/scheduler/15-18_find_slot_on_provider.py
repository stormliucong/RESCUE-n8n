"""
Evaluation Prompt:

15. 
Find slots from a recent available provider 

16.
Find  slots from an available provider who is female, speaks english and is in Boston.

17. 
Find recent slots for immunization

18.
Find available slots from provider John Smith
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


# 15
## Search for Slot resources with status "free"
print("1. Searching for Slot resources with status 'free'...")

params = {"status": "free"}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Resource found successfully. Response:")
print(response_data)

# 16
# Find prcatitioner find  slots from an available provider who is female, and is in Boston.
# TODO: fail to add practitioner who speaks english
print("2. Searching for practitioner with specific criteria...")
params = {"gender": "female", "address-city": "Boston"}

practitioner = requests.get(
    f"{FHIR_SERVER_URL}/Practitioner", headers=HEADERS, params=params
)

# Verify the response status code
assert (
    practitioner.status_code == 200
), f"Expected status code 200, but got {practitioner.status_code}. Response body: {practitioner.text}"

print("Resource found successfully. Response:")
print(practitioner.json())

practitioner_id = practitioner.json()["entry"][0]["resource"]["id"]

params = {"actor": f"Practitioner/{practitioner_id}"}

schedule_response = requests.get(
    f"{FHIR_SERVER_URL}/Schedule", headers=HEADERS, params=params
)

# Verify the response status code
assert (
    schedule_response.status_code == 200
), f"Expected status code 200, but got {schedule_response.status_code}. Response body: {schedule_response.text}"

schedule_data = schedule_response.json()
print("Schedule resource found successfully. Response:")
print(schedule_data)

# Extract the schedule ID
schedule_id = schedule_data["entry"][0]["resource"]["id"]

# Update the search parameters to find slots based on the schedule
params = {"schedule": f"Schedule/{schedule_id}", "status": "free"}


response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
# Optionally, inspect the response content
response_data = response.json()
print("Slot found successfully. Response:")
print(response_data)


# 17
print("3. Searching for recent slots for immunization...")

# Define search parameters for slots related to immunization
params = {"service-type": "Immunization", "status": "free"}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

# Optionally, inspect the response content
response_data = response.json()
print("Recent slots for immunization found successfully. Response:")
print(response_data)


# 18
print("Searching for available slots from provider John Smith...")

# Define search parameters for practitioner named John Smith
params = {"family": "Smith", "given": "Jane"}

practitioner_response = requests.get(
    f"{FHIR_SERVER_URL}/Practitioner", headers=HEADERS, params=params
)

# Verify the response status code
assert (
    practitioner_response.status_code == 200
), f"Expected status code 200, but got {practitioner_response.status_code}. Response body: {practitioner_response.text}"

practitioner_data = practitioner_response.json()
print("Practitioner resource found successfully. Response:")
print(practitioner_data)

# Extract the practitioner ID
practitioner_id = practitioner_data["entry"][0]["resource"]["id"]

# Search for schedules associated with the practitioner
params = {"actor": f"Practitioner/{practitioner_id}"}

schedule_response = requests.get(
    f"{FHIR_SERVER_URL}/Schedule", headers=HEADERS, params=params
)

# Verify the response status code
assert (
    schedule_response.status_code == 200
), f"Expected status code 200, but got {schedule_response.status_code}. Response body: {schedule_response.text}"

schedule_data = schedule_response.json()
print("Schedule resource found successfully. Response:")
print(schedule_data)

# Extract the schedule ID
schedule_id = schedule_data["entry"][0]["resource"]["id"]
# Search for available slots based on the schedule
params = {"schedule": f"Schedule/{schedule_id}", "status": "free"}

slot_response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# Verify the response status code
assert (
    slot_response.status_code == 200
), f"Expected status code 200, but got {slot_response.status_code}. Response body: {slot_response.text}"

slot_data = slot_response.json()
print("Available slots from provider John Smith found successfully. Response:")
print(slot_data)


# Empty cases:
# 1. No slots available
print("1. Searching for Slot resources with status 'free'...")

params = {"start": "le2025-04-11T00:00:00Z", "status": "free"}

response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)

# verify if the response is empty
assert (
    response.status_code == 200
), f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert not response_data.get(
    "entry"
), f"Expected no slot, but found: {response_data.get('entry')}"
print("No slot found available for the patient.")
