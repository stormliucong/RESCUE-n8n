"""
Evaluation Prompt:

11a.
Find most recent available slots from any providers

11b.
Find most recent available slots from a provider who is a female, speaks english and is located in Boston.

11c.
Find the most recent available slots for a genetic counseling service

11d.
Find the most recent available slots for Dr. John Smith

"""

from datetime import datetime, timedelta
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
practitioner = {
    "resourceType": "Practitioner",
    "id": "PROVIDER001",
    "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
    "gender": "male",
    "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
    "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
}

# Add more practitioners with diverse attributes
practitioner2 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER002",
    "name": [{"use": "official", "family": "Chen", "given": ["Wei"]}],
    "gender": "female",
    "communication": [
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "zh"}]}
    ],
    "address": [{"use": "work", "line": ["456 Oak Ave"], "city": "New York", "state": "NY"}],
}

practitioner3 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER003",
    "name": [{"use": "official", "family": "Garcia", "given": ["Maria", "Isabel"]}],
    "gender": "female",
    "communication": [
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "es"}]}
    ],
    "address": [{"use": "work", "line": ["789 Pine St"], "city": "Los Angeles", "state": "CA"}],
}

practitioner4 = {
    "resourceType": "Practitioner",
    "id": "PROVIDER004",
    "name": [{"use": "official", "family": "Patel", "given": ["Rajesh"]}],
    "gender": "male",
    "communication": [
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
        {"coding": [{"system": "urn:ietf:bcp:47", "code": "hi"}]}
    ],
    "address": [{"use": "work", "line": ["321 Elm St"], "city": "Chicago", "state": "IL"}],
}

# Upsert all practitioners to FHIR server
upsert_to_fhir(practitioner)
upsert_to_fhir(practitioner2)
upsert_to_fhir(practitioner3)
upsert_to_fhir(practitioner4)

schedule = {
    "resourceType": "Schedule",
    "id": "SCHEDULE001",
    "actor": [{"reference": "Practitioner/PROVIDER001"}],
    "planningHorizon": {
        "start": "2025-04-11T00:00:00Z",
        "end": "2026-04-11T00:00:00Z"
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}

upsert_to_fhir(schedule)
schedule2 = {
    "resourceType": "Schedule",
    "id": "SCHEDULE002",
    "actor": [{"reference": "Practitioner/PROVIDER002"}],
    "planningHorizon": {
        "start": "2025-04-11T00:00:00Z",
        "end": "2026-04-11T00:00:00Z"
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "408459003", "display": "Pediatric cardiology"}]}],
}
upsert_to_fhir(schedule2)

schedule3 = {
    "resourceType": "Schedule",
    "id": "SCHEDULE003",
    "actor": [{"reference": "Practitioner/PROVIDER003"}],
    "planningHorizon": {
        "start": "2025-04-11T00:00:00Z",
        "end": "2026-04-11T00:00:00Z"
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}
upsert_to_fhir(schedule3)

schedule4 = {
    "resourceType": "Schedule",
    "id": "SCHEDULE004",
    "actor": [{"reference": "Practitioner/PROVIDER004"}],
    "planningHorizon": {
        "start": "2025-04-11T00:00:00Z",
        "end": "2026-04-11T00:00:00Z"
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}
upsert_to_fhir(schedule4)

j = 1
for k in range(4):
    for i in range(9, 16):
        schedule_id = f"SCHEDULE00{k+1}"
        start = datetime.now() + timedelta(days=1)
        start = start.replace(hour=i, minute=0, second=0, microsecond=0)
        # convert it to 2025-04-11T00:00:00Z
        # end is tomorrow at 9am
        end = start + timedelta(hours=1)
        # convert it to 2025-04-11T00:00:00Z
        start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        end = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        # status is free for even i, busy for odd i
        status = "free" if (i+k) % 4 == 0 else "busy" 
        slot = {
            "resourceType": "Slot",
            "id": f"SLOT00{j}",
            "schedule": {"reference": f"Schedule/{schedule_id}"},
            "start": start,
            "end": end,
            "status": status
        }    
        upsert_to_fhir(slot)
        j += 1
        
# Expected actions for agent
# 11a.
params = {
    "status": "free",
}
response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one slot, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one slot, but got {len(response.json()['entry'])}"
# arrange the slots by start time
# find earliest start time and the schedule id
earliest_start_time = min(response.json()['entry'], key=lambda x: x['resource']['start'])['resource']['start']
schedule_id = min(response.json()['entry'], key=lambda x: x['resource']['start'])['resource']['schedule']['reference'].split('/')[1]
assert schedule_id == "SCHEDULE004", f"Expected schedule id to be SCHEDULE004, but got {schedule_id}"











