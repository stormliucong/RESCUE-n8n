"""
Evaluation Prompt:

13a.
Find the patient who has booked the Dr. John Smith's slots next Monday morning at 9am.

13b.
Find the patient who has booked the Dr. Smith John's slots next Monday morning at 9am.

"""
import requests
from generate_schedule_sync_data import (
    create_patient,
    upsert_to_fhir,
    delete_all_resources,
    create_practitioner,
    create_schedule,
    create_location,
    create_appointment,
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


practitioner2 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER002",
    "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
}
upsert_to_fhir(practitioner2)   

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
    "status": "busy",
    "schedule": {"reference": "Schedule/SCHEDULE002"},
}
upsert_to_fhir(slot2)

appointment2 = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT002",
    "status": "booked",
    "slot": [{"reference": "Slot/SLOT002"}],
    "participant": [{"actor": {"reference": "Patient/PAT002"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER002"}, "status": "accepted"}],
}
upsert_to_fhir(appointment2)

# Expected actions for agent
# 13a.
params={"family": "Smith", "given": "John"}
response = requests.get(f"{FHIR_SERVER_URL}/Practitioner", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one practitioner, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one practitioner, but got {len(response.json()['entry'])}"

practitioner_id = response.json()['entry'][0]['resource']['id']
assert practitioner_id == "PROVIDER001", f"Expected provider id to be PROVIDER001, but got {practitioner_id}"
params = {"practitioner": f"Practitioner/{practitioner_id}"}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one appointment, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one appointment, but got {len(response.json()['entry'])}"

patient_id = response.json()['entry'][0]['resource']['participant'][0]['actor']['reference']
assert patient_id == "Patient/PAT001", f"Expected patient id to be PAT001, but got {patient_id}"
response = requests.get(f"{FHIR_SERVER_URL}/{patient_id}", headers=HEADERS)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'name' in response.json(), f"Expected to find name in the response"
assert len(response.json()['name']) > 0, f"Expected to find at least one name, but got {len(response.json()['name'])}"
given_name = response.json()['name'][0]['given'][0]
assert given_name == "John", f"Expected given name to be John, but got {given_name}"
family_name = response.json()['name'][0]['family']
assert family_name == "Doe", f"Expected family name to be Doe, but got {family_name}"

# 13b.
params={"family": "John", "given": "Smith"}
response = requests.get(f"{FHIR_SERVER_URL}/Practitioner", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one practitioner, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one practitioner, but got {len(response.json()['entry'])}"

practitioner_id = response.json()['entry'][0]['resource']['id']
assert practitioner_id == "PROVIDER002", f"Expected provider id to be PROVIDER002, but got {practitioner_id}"
params = {"practitioner": f"Practitioner/{practitioner_id}"}
response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one appointment, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one appointment, but got {len(response.json()['entry'])}"

patient_id = response.json()['entry'][0]['resource']['participant'][0]['actor']['reference']
assert patient_id == "Patient/PAT002", f"Expected patient id to be PAT002, but got {patient_id}"
response = requests.get(f"{FHIR_SERVER_URL}/{patient_id}", headers=HEADERS)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'name' in response.json(), f"Expected to find name in the response"
assert len(response.json()['name']) > 0, f"Expected to find at least one name, but got {len(response.json()['name'])}"
given_name = response.json()['name'][0]['given'][0]
assert given_name == "Jane", f"Expected given name to be Jane, but got {given_name}"
family_name = response.json()['name'][0]['family']
assert family_name == "Doe", f"Expected family name to be Doe, but got {family_name}"








