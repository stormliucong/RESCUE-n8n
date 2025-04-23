"""
Evaluation Prompt:

15a. Cancel Patient John Doe's next coming appointment

15b. Cancel Patient John Doe's next coming appointment with Dr. Smith John

15c. Cancer Patient John Doe's appointment on next Monday.
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
from datetime import datetime, timedelta
load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")

HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

delete_all_resources()  # Clean up existing resources before the test
patient1 = {
    "resourceType": "Patient",
    "id": "PAT001",
    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
    "birthDate": "1990-06-15",
    "telecom": [{"system": "phone", "value": "123-456-7890"}],
    "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
}
upsert_to_fhir(patient1)
practitioner1 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER001",
    "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
    "gender": "male",
    "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
    "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
}
upsert_to_fhir(practitioner1)
practitioner2 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER002",
    "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
    "gender": "male",
    "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
}
upsert_to_fhir(practitioner2)
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

# next monday at 9am with provider 1
start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
start = start.replace(hour=9, minute=0, second=0, microsecond=0)
slot1 = {
    "resourceType": "Slot",
    "id": "SLOT001",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "status": "busy",
    "schedule": {"reference": "Schedule/SCHEDULE001"},
}
upsert_to_fhir(slot1)
appointment1 = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT001",
    "status": "booked",
    "slot": [{"reference": "Slot/SLOT001"}],
    "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
}
upsert_to_fhir(appointment1)

# next Tuesday at 9am with provider 2
start = start + timedelta(days=1)
start = start.replace(hour=9, minute=0, second=0, microsecond=0)
slot2 = {
    "resourceType": "Slot",
    "id": "SLOT002",
    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "status": "busy",
    "schedule": {"reference": "Schedule/SCHEDULE002"},
}
upsert_to_fhir(slot2)
appointment2 = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT002",
    "status": "booked",
    "slot": [{"reference": "Slot/SLOT002"}],
    "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER002"}, "status": "accepted"}],
}
upsert_to_fhir(appointment2)

# Expected actions for agent
# 15a.
params = {
    "patient": "Patient/PAT001",
    "status": "booked",
}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one appointment, but got {response.json()['total']}"
appointment_to_cancel = None
earliest_start_date = datetime.max
for appointment in response.json()['entry']:
    # find the appointment with the earliest start date
    # find the slot and query slot to get the start date
    slot = appointment['resource']['slot'][0]['reference']
    slot_response = requests.get(f"{FHIR_SERVER_URL}/{slot}", headers=HEADERS)
    assert slot_response.status_code == 200, f"Expected status code 200, but got {slot_response.status_code}. Response body: {slot_response.text}"
    start_date = slot_response.json()['start']
    # TypeError: '<' not supported between instances of 'str' and 'datetime.datetime'
    if datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ") < earliest_start_date:
        earliest_start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
        appointment_to_cancel = appointment
assert appointment_to_cancel is not None, f"Expected to find an appointment to cancel, but did not find one"
assert appointment_to_cancel['resource']['id'] == 'APPOINTMENT001', f"Expected to find appointment 1 to cancel, but found {appointment_to_cancel['resource']['id']}"

# 15b.
params = {
    "patient": "Patient/PAT001",
    "status": "booked",
    "practitioner": "Practitioner/PROVIDER002",
}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one appointment, but got {response.json()['total']}"
appointment_to_cancel = None
earliest_start_date = datetime.max
for appointment in response.json()['entry']:
    # find the appointment with the earliest start date
    slot = appointment['resource']['slot'][0]['reference']
    slot_response = requests.get(f"{FHIR_SERVER_URL}/{slot}", headers=HEADERS)
    assert slot_response.status_code == 200, f"Expected status code 200, but got {slot_response.status_code}. Response body: {slot_response.text}"
    start_date = slot_response.json()['start']
    if datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ") < earliest_start_date:
        earliest_start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
        appointment_to_cancel = appointment
assert appointment_to_cancel is not None, f"Expected to find an appointment to cancel, but did not find one"    
assert appointment_to_cancel['resource']['id'] == 'APPOINTMENT002', f"Expected to find appointment 2 to cancel, but found {appointment_to_cancel['resource']['id']}"

# 15c.
next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
params = {
    "patient": "Patient/PAT001",
    "status": "booked",
    "practitioner": "Practitioner/PROVIDER001",
}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one appointment, but got {response.json()['total']}"
appointment_to_cancel = None
next_monday_time = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
# convert it to date.
next_monday_date = next_monday_time.date()
for appointment in response.json()['entry']:
    # find the appointment on next monday
    slot = appointment['resource']['slot'][0]['reference']
    slot_response = requests.get(f"{FHIR_SERVER_URL}/{slot}", headers=HEADERS)
    start_datetime = slot_response.json()['start']
    # convert it to date.
    start_date = datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M:%SZ").date()
    if start_date == next_monday_date:
        appointment_to_cancel = appointment
assert appointment_to_cancel is not None, f"Expected to find an appointment to cancel, but did not find one"
assert appointment_to_cancel['resource']['id'] == 'APPOINTMENT001', f"Expected to find appointment 1 to cancel, but found {appointment_to_cancel['resource']['id']}"