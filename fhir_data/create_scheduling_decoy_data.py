# In this simulation, the script will
# Create three Practitioner resources.
# Create three Patient resources.
# For each Practitioner, create a Schedule and three Slot resources.
# For each Practitioner–Patient pairing (by index), book an Appointment for the patient using one of that provider’s slots.


#!/usr/bin/env python3
import requests
import json
import base64

# Your credentials
username = "f54370de-eaf3-4d81-a17e-24860f667912"
password = "75d8e7d06bf9283926c51d5f461295ccf0b69128e983b6ecdd5a9c07506895de"

# Encode credentials
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()


# Base URL for your FHIR server
FHIR_SERVER = "http://localhost:8103/fhir/R4"
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json",
    "Authorization": f"Basic {encoded_credentials}"
}

def create_resource(resource_type, payload):
    """
    Create a FHIR resource of the given type with the provided payload.
    Returns the resource ID if creation was successful.
    """
    url = f"{FHIR_SERVER}/{resource_type}"
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code not in (200, 201):
        print(f"Error creating {resource_type}: {response.status_code} {response.text}")
        return None

    try:
        resource = response.json()
        resource_id = resource.get("id")
    except json.JSONDecodeError:
        resource_id = None

    # Fallback: try to extract the ID from the Location header if not in the JSON
    if not resource_id:
        location = response.headers.get("Location")
        if location:
            resource_id = location.rstrip("/").split("/")[-1]

    print(f"Created {resource_type} with id: {resource_id}")
    return resource_id

def main():
    # Define three practitioners with three available slots each
    practitioners = [
        {
            "name": "Genetic Specialist 001",
            "practitioner_payload": {
                "resourceType": "Practitioner",
                "identifier": [
                    {"system": "http://example.org/providers", "value": "genetic-specialist-001"}
                ],
                "name": [
                    {"family": "Specialist", "given": ["Genetic001"]}
                ],
                "qualification": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "408478003",
                                    "display": "Genetic Specialist"
                                }
                            ]
                        }
                    }
                ]
            },
            "slots": [
                {"start": "2025-02-13T09:00:00Z", "end": "2025-02-13T09:30:00Z"},
                {"start": "2025-02-13T09:30:00Z", "end": "2025-02-13T10:00:00Z"},
                {"start": "2025-02-13T10:00:00Z", "end": "2025-02-13T10:30:00Z"}
            ]
        },
        {
            "name": "Genetic Specialist 002",
            "practitioner_payload": {
                "resourceType": "Practitioner",
                "identifier": [
                    {"system": "http://example.org/providers", "value": "genetic-specialist-002"}
                ],
                "name": [
                    {"family": "Specialist", "given": ["Genetic002"]}
                ],
                "qualification": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "408478003",
                                    "display": "Genetic Specialist"
                                }
                            ]
                        }
                    }
                ]
            },
            "slots": [
                {"start": "2025-02-13T11:00:00Z", "end": "2025-02-13T11:30:00Z"},
                {"start": "2025-02-13T11:30:00Z", "end": "2025-02-13T12:00:00Z"},
                {"start": "2025-02-13T12:00:00Z", "end": "2025-02-13T12:30:00Z"}
            ]
        },
        {
            "name": "Genetic Specialist 003",
            "practitioner_payload": {
                "resourceType": "Practitioner",
                "identifier": [
                    {"system": "http://example.org/providers", "value": "dermatology-specialist-003"}
                ],
                "name": [
                    {"family": "Specialist", "given": ["Genetic003"]}
                ],
                "qualification": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "408478003",
                                    "display": "Genetic Specialist"
                                }
                            ]
                        }
                    }
                ]
            },
            "slots": [
                {"start": "2025-02-13T13:00:00Z", "end": "2025-02-13T13:30:00Z"},
                {"start": "2025-02-13T13:30:00Z", "end": "2025-02-13T14:00:00Z"},
                {"start": "2025-02-13T14:00:00Z", "end": "2025-02-13T14:30:00Z"}
            ]
        }
    ]

    # Define three patients
    patients = [
        {
            "name": "Alice Test",
            "patient_payload": {
                "resourceType": "Patient",
                "identifier": [
                    {"system": "http://example.org/patients", "value": "alice-patient-001"}
                ],
                "name": [
                    {"family": "Patient", "given": ["Alice"]}
                ]
            }
        },
        {
            "name": "Bob Test",
            "patient_payload": {
                "resourceType": "Patient",
                "identifier": [
                    {"system": "http://example.org/patients", "value": "bob-patient-001"}
                ],
                "name": [
                    {"family": "Patient", "given": ["Bob"]}
                ]
            }
        },
        {
            "name": "Charlie Test",
            "patient_payload": {
                "resourceType": "Patient",
                "identifier": [
                    {"system": "http://example.org/patients", "value": "charlie-patient-001"}
                ],
                "name": [
                    {"family": "Patient", "given": ["Charlie"]}
                ]
            }
        }
    ]

    # Common planning horizon for all schedules
    planning_horizon = {
        "start": "2025-02-13T08:00:00Z",
        "end": "2025-02-14T17:00:00Z"
    }

    # Hold our created resources
    practitioner_results = []  # list of dicts with keys: name, practitioner_id, schedule_id, slots (a list of dicts with id, start, end)
    for provider in practitioners:
        print(f"\nCreating Practitioner: {provider['name']}")
        practitioner_id = create_resource("Practitioner", provider["practitioner_payload"])
        if not practitioner_id:
            continue

        # Create Schedule for the Practitioner
        schedule_payload = {
            "resourceType": "Schedule",
            "actor": [{"reference": f"Practitioner/{practitioner_id}"}],
            "planningHorizon": planning_horizon
        }
        schedule_id = create_resource("Schedule", schedule_payload)
        if not schedule_id:
            continue

        # Create Slot resources for this practitioner's schedule
        slot_details = []  # list of dicts: { "id": ..., "start": ..., "end": ... }
        for slot in provider["slots"]:
            slot_payload = {
                "resourceType": "Slot",
                "status": "free",
                "start": slot["start"],
                "end": slot["end"],
                "schedule": {"reference": f"Schedule/{schedule_id}"}
            }
            slot_id = create_resource("Slot", slot_payload)
            if slot_id:
                slot_details.append({
                    "id": slot_id,
                    "start": slot["start"],
                    "end": slot["end"]
                })

        practitioner_results.append({
            "name": provider["name"],
            "practitioner_id": practitioner_id,
            "schedule_id": schedule_id,
            "slots": slot_details
        })

    # Create Patient resources
    patient_results = []  # list of dicts: { "name": ..., "patient_id": ... }
    for patient in patients:
        print(f"\nCreating Patient: {patient['name']}")
        patient_id = create_resource("Patient", patient["patient_payload"])
        if patient_id:
            patient_results.append({
                "name": patient["name"],
                "patient_id": patient_id
            })

    # Create Appointments:
    # For this simulation, we map each patient (by index) to the corresponding practitioner (by index)
    # and book an appointment using the first available slot of that practitioner's schedule.
    for idx, patient in enumerate(patient_results):
        if idx >= len(practitioner_results):
            print("Not enough practitioners for all patients.")
            break

        provider = practitioner_results[idx]
        if not provider["slots"]:
            print(f"No available slots for provider {provider['name']}")
            continue

        # Select the first available slot for this provider
        chosen_slot = provider["slots"][0]

        appointment_payload = {
            "resourceType": "Appointment",
            "status": "booked",
            "description": f"Appointment for {patient['name']} with {provider['name']}",
            "start": chosen_slot["start"],
            "end": chosen_slot["end"],
            "participant": [
                {
                    "actor": {
                        "reference": f"Patient/{patient['patient_id']}",
                        "display": patient["name"]
                    },
                    "status": "accepted"
                },
                {
                    "actor": {
                        "reference": f"Practitioner/{provider['practitioner_id']}",
                        "display": provider["name"]
                    },
                    "status": "accepted"
                }
            ],
            "slot": [
                {"reference": f"Slot/{chosen_slot['id']}"}
            ]
        }
        print(f"\nCreating Appointment for patient {patient['name']} with provider {provider['name']} (Slot: {chosen_slot['id']})")
        create_resource("Appointment", appointment_payload)

    print("\nAll resources created and appointments booked.")

if __name__ == "__main__":
    main()
