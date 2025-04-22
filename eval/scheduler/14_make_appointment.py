"""
Evaluation Prompt:

14a.
Make an appointment time for the patient John Doe with Provider Dr. John Smith on next Monday morning at 9am.

14b.
Make an appointment time for the patient Jane Doe with Provider Dr. Smith Johnon next Monday morning at 9am.

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
from datetime import datetime, timedelta

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

delete_all_resources()  # Clean up existing resources before the test
practitioner1 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER001",
    "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
    "gender": "male",
    "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
    "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
}
upsert_to_fhir(practitioner1)
start = datetime.now()
end = start + timedelta(days=365)
schedule1 = {
    "resourceType": "Schedule",
    "id": "SCHEDULE001",
    "actor": [{"reference": "Practitioner/PROVIDER001"}],
    "planningHorizon": {
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}
upsert_to_fhir(schedule1)
patient1 = {
    "resourceType": "Patient",
    "id": "PAT001",
    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
    "birthDate": "1990-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
upsert_to_fhir(patient1)
start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
start = start.replace(hour=9, minute=0, second=0, microsecond=0)
slot1 = {
    "resourceType": "Slot",
    "id": "SLOT001",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "status": "free",
    "schedule": {"reference": "Schedule/SCHEDULE001"},
}
upsert_to_fhir(slot1)



practitioner2 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER002",
    "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
}
upsert_to_fhir(practitioner2)   
start = datetime.now()
end = start + timedelta(days=365)
schedule2 = {
    "resourceType": "Schedule",
    "id": "SCHEDULE002",
    "actor": [{"reference": "Practitioner/PROVIDER002"}],
    "planningHorizon": {
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}
upsert_to_fhir(schedule2)
patient2 = {
    "resourceType": "Patient",
    "id": "PAT002",
    "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
    "birthDate": "2020-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
upsert_to_fhir(patient2)
start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
start = start.replace(hour=9, minute=0, second=0, microsecond=0)
slot2 = {
    "resourceType": "Slot",
    "id": "SLOT002",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "status": "free",
    "schedule": {"reference": "Schedule/SCHEDULE002"},
}
upsert_to_fhir(slot2)

# Expected actions for agent
# 14a.
params = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT001",
    "status": "booked",
    "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
    "slot": "Slot/SLOT001",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
response = requests.post(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, json=params)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
print(response.json())
params = {
    "resourceType": "Slot",
    "id": "SLOT001",
    "status": "busy",
}
response = requests.put(f"{FHIR_SERVER_URL}/Slot/SLOT001", headers=HEADERS, json=params)
assert response.status_code == 200, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
print(response.json())

# 14b.
params = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT002",
    "status": "booked",
    "participant": [{"actor": {"reference": "Patient/PAT002"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER002"}, "status": "accepted"}],
    "slot": "Slot/SLOT002",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
response = requests.post(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, json=params)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
print(response.json())
params = {
    "resourceType": "Slot",
    "id": "SLOT002",
    "status": "busy",
}
response = requests.put(f"{FHIR_SERVER_URL}/Slot/SLOT002", headers=HEADERS, json=params)
assert response.status_code == 200, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
print(response.json())


