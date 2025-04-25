"""
Evaluation Prompt:
16a. Patient John Doe id=PAT001 wants an earlier time with Dr. Smith. Add them to the waitlist.
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
    create_appointment
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
# create slots for next 14 days, morning available only.
j = 1
for x in range(14):
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
            # for first 7 days is always busy
            # for rest of the days is always free.
            status = "busy" if x < 7 else "free"
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
            
# Create a current appointment for patient 1


# Expected actions for agent
# 16a.
start = datetime.now() + timedelta(days=1)
end = datetime.now() + timedelta(days=6)
params = {
    "resourceType": "Appointment",
    "id": "APPOINTMENT001",
    "status": "waitlist",
    "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
    "requestedPeriod": {
        "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
}
response = requests.post(f"{FHIR_SERVER_URL}/Appointment", headers=HEADERS, json=params)
assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
print(response.json())




