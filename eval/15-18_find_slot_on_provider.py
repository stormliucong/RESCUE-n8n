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
TODO: finish test script for other 2 cases
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

# Find prcatitioner find  slots from an available provider who is female, and is in Boston.
print("2. Searching for practitioner with specific criteria...")
params = {"gender": "female", "address-city": "Boston"}

practitioner = requests.get(f"{FHIR_SERVER_URL}/Practitioner", headers=HEADERS, params=params)

# Verify the response status code
assert (
    practitioner.status_code == 200
), f"Expected status code 200, but got {practitioner.status_code}. Response body: {practitioner.text}"

print("Resource found successfully. Response:")
print(practitioner.json())

practitioner_id = practitioner.json()["entry"][0]["resource"]["id"]

params = {"actor": f"Practitioner/{practitioner_id}"}

schedule_response = requests.get(f"{FHIR_SERVER_URL}/Schedule", headers=HEADERS, params=params)

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

