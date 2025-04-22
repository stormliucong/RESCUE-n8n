"""
Evaluation Prompt:
12a.
Patient needs a urgent visit by the end of tomorrow. Find all available slots for him.

12b.
Patient needs a general visit on next Friday. Find all available slots for him.

12c.
Find any available follow-up slots for a patient about one month from now.

12d.
Patients needs a visit on any Wednesday morning before 12pm one months from now. Find all available slots for him.
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

# Upsert all practitioners to FHIR server
upsert_to_fhir(practitioner)

start = datetime.now()
end = start + timedelta(days=365)
schedule = {
    "resourceType": "Schedule",
    "id": "SCHEDULE001",
    "actor": [{"reference": "Practitioner/PROVIDER001"}],
    "planningHorizon": {
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
    },
    "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
}
upsert_to_fhir(schedule)

j = 1
for x in range(35):
    # reduce resources using, morning available only.
    for i in range(9, 12):
        schedule_id = f"SCHEDULE001"
        start = datetime.now() + timedelta(days=x)
        # determine if it is a weekday or weekend
        if start.weekday() < 5:
            start = start.replace(hour=i, minute=0, second=0, microsecond=0)
            # convert it to 2025-04-11T00:00:00Z
            # end is tomorrow at 9am
            end = start + timedelta(hours=1)
            # convert it to 2025-04-11T00:00:00Z
            start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
            end = end.strftime("%Y-%m-%dT%H:%M:%SZ")
            # status is free for even i, busy for odd i
            status = "free" if i % 2 == 0 else "busy"
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
# 12a.
start = datetime.now()
end = start + timedelta(days=1)
params = {
    "start": [f'gt{start.strftime("%Y-%m-%dT%H:%M:%SZ")}', f'lt{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'],
    "status": "free",
}
response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
if start.weekday() in [0, 1, 2, 3]:
    print(f'Today is {["Monday", "Tuesday", "Wednesday", "Thursday"][start.weekday()]}')
    assert 'total' in response.json(), f"Expected to find total in the response"
    assert response.json()['total'] > 0, f"Expected to find at least one slot, but got {response.json()['total']}"
    assert 'entry' in response.json(), f"Expected to find entry in the response"
    assert len(response.json()['entry']) > 0, f"Expected to find at least one slot, but got {len(response.json()['entry'])}"
else:
    print(f'Today is {["Friday", "Saturday", "Sunday"][start.weekday()]}, this test is not applicable')

# 12b.
start = datetime.now() + timedelta(days=7)
next_friday = start + timedelta(days=(4 - start.weekday()) % 7)
assert next_friday.weekday() == 4, f"Expected next friday to be a friday, but got {next_friday.weekday()}"
start = next_friday.replace(hour=9, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)
params = {
    "start": [f'ge{start.strftime("%Y-%m-%dT%H:%M:%SZ")}',f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'],
    "status": "free",
}
response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
print(f'Next friday is {next_friday.strftime("%Y-%m-%d")}')
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one slot, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) == 1, f"Expected to find one slot, but got {len(response.json()['entry'])}"

# 12c.
start = datetime.now() + timedelta(days=30)
# if start is a weekend, then change start to the next weekday
if start.weekday() > 4:
    start = start + timedelta(days=(7 - start.weekday()))
start = start.replace(hour=9, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)

params = {
    "start": [f'ge{start.strftime("%Y-%m-%dT%H:%M:%SZ")}', f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'],
    "status": "free",
}
response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
print(f'About one month from now is {start.strftime("%Y-%m-%d")}')
assert 'total' in response.json(), f"Expected to find total in the response"
assert response.json()['total'] > 0, f"Expected to find at least one slot, but got {response.json()['total']}"
assert 'entry' in response.json(), f"Expected to find entry in the response"
assert len(response.json()['entry']) > 0, f"Expected to find at least one slot, but got {len(response.json()['entry'])}"

# 12d.
for delta in range(1, 30):
    start = datetime.now() + timedelta(days=delta)
    if start.weekday() == 2:
        start = start.replace(hour=9, minute=0, second=0, microsecond=0)
        end = start.replace(hour=12, minute=0, second=0, microsecond=0)
        params = {
            "start": [f'ge{start.strftime("%Y-%m-%dT%H:%M:%SZ")}', f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'],
            "status": "free",
        }
        response = requests.get(f"{FHIR_SERVER_URL}/Slot", headers=HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'total' in response.json(), f"Expected to find total in the response"
        assert response.json()['total'] > 0, f"Expected to find at least one slot, but got {response.json()['total']}"
        assert 'entry' in response.json(), f"Expected to find entry in the response"
        assert len(response.json()['entry']) > 0, f"Expected to find at least one slot, but got {len(response.json()['entry'])}"
        print(f'We found {["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][start.weekday()]} morning slots for {start.strftime("%Y-%m-%d")}')
        print(f'start: {response.json()["entry"][0]["resource"]["start"]}')
        print(f'end: {response.json()["entry"][0]["resource"]["end"]}')

        # push to the response list.