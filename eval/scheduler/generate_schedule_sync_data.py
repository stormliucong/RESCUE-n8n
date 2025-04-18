# This is for schedule agent testing purposes.

import requests
import random
from faker import Faker
import logging
import time


# Set a global seed
SEED = 0

# Set the seed for random
random.seed(SEED)

# Set the seed for Faker
faker = Faker()

import os
from dotenv import load_dotenv

load_dotenv()

FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
HEADERS = {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}

RESOURCE_TYPES = [
    "Patient",
    "Condition",
    "Procedure",
    "Coverage",
    "Practitioner",
    "Organization",
    "RelatedPerson",
    "Consent",
    "DocumentReference",
    "Slot",
    "Schedule",
    "Appointment",
]


def get_resource_ids(resource_type):
    """Fetches all resource IDs for the given resource type."""
    url = f"{FHIR_SERVER_URL}/{resource_type}?_count=100"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Failed to fetch {resource_type}: {response.status_code}")
        return []

    data = response.json()
    if "entry" not in data:
        return []

    return [entry["resource"]["id"] for entry in data["entry"]]


def delete_resource(resource_type, resource_id):
    """Deletes a specific resource by ID, removing any references to it first."""
    # First, find and remove any references to this resource
    search_url = f"{FHIR_SERVER_URL}/{resource_type}/_search"
    search_params = {
        "_query": "has-reference",
        "reference": f"{resource_type}/{resource_id}"
    }
    response = requests.post(search_url, params=search_params, headers=HEADERS)
    
    if response.status_code == 200:
        search_results = response.json()
        if 'entry' in search_results:
            for entry in search_results['entry']:
                referencing_resource = entry['resource']
                # Remove the reference from the resource
                for field in referencing_resource:
                    if isinstance(referencing_resource[field], dict) and 'reference' in referencing_resource[field]:
                        if referencing_resource[field]['reference'] == f"{resource_type}/{resource_id}":
                            referencing_resource[field] = None
                    elif isinstance(referencing_resource[field], list):
                        for item in referencing_resource[field]:
                            if isinstance(item, dict) and 'reference' in item:
                                if item['reference'] == f"{resource_type}/{resource_id}":
                                    item['reference'] = None
                
                # Update the referencing resource
                update_url = f"{FHIR_SERVER_URL}/{referencing_resource['resourceType']}/{referencing_resource['id']}"
                update_response = requests.put(update_url, json=referencing_resource, headers=HEADERS)
                if update_response.status_code not in [200, 201]:
                    print(f"Failed to update referencing resource {referencing_resource['resourceType']}/{referencing_resource['id']}: {update_response.text}")
    
    # Now delete the resource
    url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
    response = requests.delete(url, headers=HEADERS)

    if response.status_code in [200, 204]:
        print(f"Deleted {resource_type}/{resource_id}")
    else:
        print(f"Failed to delete {resource_type}/{resource_id}: {response.text}")


def delete_all_resources():
    """Deletes all resources of the specified types in the correct order to handle dependencies."""
    # Define the order of deletion based on dependencies
    # Resources that depend on others should be deleted first
    deletion_order = [
        "Appointment",      # Depends on Patient, Practitioner, Location, Slot
        "Slot",            # Depends on Schedule
        "Schedule",        # Depends on Practitioner
        "DocumentReference", # Depends on Patient, Practitioner
        "Consent",         # Depends on Patient, Organization, DocumentReference
        "Account",         # Depends on Patient, RelatedPerson
        "RelatedPerson",   # Depends on Patient
        "Coverage",        # Depends on Patient, Organization
        "Procedure",       # Depends on Patient
        "Condition",       # Depends on Patient
        "ServiceRequest",  # Depends on Patient
        "CarePlan",        # Depends on Patient, Encounter
        "Location",        # No dependencies
        "Practitioner",    # No dependencies
        "Organization",    # No dependencies
        "Patient",         # No dependencies
    ]

    for resource_type in deletion_order:
        print(f"\nProcessing {resource_type} resources...")
        resource_ids = get_resource_ids(resource_type)

        if not resource_ids:
            print(f"No {resource_type} resources found.")
            continue

        print(f"Deleting {len(resource_ids)} {resource_type} resources...")
        for resource_id in resource_ids:
            delete_resource(resource_type, resource_id)
            # Add a small delay to prevent overwhelming the server
            time.sleep(0.1)

def create_patient(resource=None):
    """
    Creates a Patient resource with fake data.
    """
    if resource is None:
        return {
            "resourceType": "Patient",
            "id": "PAT001",
        "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
        "birthDate": "1990-06-15",
        "telecom": [{"system": "phone", "value": "123-456-7890"}],
        "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
    }
    else:
        return resource

def create_condition(condition_resource=None, patient_id=None):
    """
    Creates a Condition resource associated with a patient.
    """
    if condition_resource is None:
        return {
            "resourceType": "Condition",
            "id": "COND001",
            "code": {"text": "Hypertension"},
            "subject": {"reference": f"Patient/{patient_id}"},
        }
    else:
        return condition_resource

def create_service_request(service_request_resource=None, patient_id=None):
    """
    Creates a ServiceRequest resource associated with a patient.
    """
    if service_request_resource is None:
        return {
            "resourceType": "ServiceRequest",
            "id": "SERVICE-REQUEST-001",
            "status": "active",
            "intent": "order",
            "subject": {"reference": f"Patient/{patient_id}"},
        }
    else:
        return service_request_resource

def create_procedure(patient_id):
    """
    Creates a Procedure resource associated with a patient.
    """
    return {
        "resourceType": "Procedure",
        "id": "PROC001",
        "status": "in-progress",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {"text": "Appendectomy"},
    }


def create_coverage(coverage_resource=None, patient_id=None):
    """
    Creates a Coverage resource associated with a patient.
    """
    if coverage_resource is None:
        return {
            "resourceType": "Coverage",
            "id": "COV001",
            "status": "active",
            "kind": "insurance",
            "subscriber": {"reference": f"Patient/{patient_id}"},
            "beneficiary": {"reference": f"Patient/{patient_id}"},
            "insurer": {"reference": "Organization/ORG123"},
        }
    else:
        return coverage_resource  


def create_practitioner():
    """
    Creates a Practitioner resource with fake data.
    """
    return {
        "resourceType": "Practitioner",
        "id": "PRACT001",
        "name": [{"family": "Smith", "given": ["Jane"]}],
        "address": [
            {
                "use": "work",
                "line": ["9 Main Ave"],
                "city": "Boston",
                "state": "MA",
                "postalCode": "02115",
                "country": "US",
            }
        ],
        "gender": "female",
        "birthDate": "1959-03-11",
        "communication": [
            {"language": {"text": "English"}}
        ],
    }


def create_organization(resource=None):
    """
    Creates an Organization resource.
    """
    if resource is None:
        return {"resourceType": "Organization", "id": "ORG001", "name": "XYZ Insurance"}
    else:
        return resource


def create_related_person(resource=None, patient_id=None):
    """
    Creates a RelatedPerson resource associated with a patient.
    """
    if resource is None:
        return {
            "resourceType": "RelatedPerson",
            "id": "REL001",
            "patient": {"reference": f"Patient/{patient_id}"},
            "relationship": [{"text": "Mother"}],
            "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
            "gender": "female",
            "birthDate": "1960-03-01",
        }
    else:
        return resource


def create_account(account_resource=None, patient_id=None):
    """
    Creates an Account resource associated with a patient.
    """
    if account_resource is None:
        return {  # TODO: decide which parameter to add
            "resourceType": "Account",
            "id": "ACC001",
            "status": "active",
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/account-type",
                        "code": "guarantor",
                        "display": "Guarantor",
                    }
                ]
            },
            "name": "Guarantor Account",
            "subject": {"reference": f"Patient/{patient_id}"},
            "guarantor": [
                    {"party": {"reference": f"RelatedPerson/REL001"}, "onHold": False}
                ],
            }
    else:
        return account_resource


def create_consent(patient_id, document_id="DOC001"):
    """
    Creates a Consent resource associated with a patient.
    """
    return {
        "resourceType": "Consent",
        "id": "CONSENT001",
        "status": "active",
        "subject": {
            "reference": f"Patient/{patient_id}",
        },
        "date": "2025-03-24",
        "controller": [{"reference": "Organization/ORG001"}],
        "sourceAttachment": [{"title": "The terms of the consent."}],
        "policyText": {
            "reference": f"DocumentReference/DOC001"
        },  # TODO: failed to add policy text
        "decision": "permit",
    }


def create_document_reference(patient_id):
    """
    Creates a DocumentReference resource associated with a patient.
    """
    return {
        "resourceType": "DocumentReference",
        "id": "DOC001",
        "status": "current",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "34108-1",
                    "display": "Outpatient Note",
                }
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "date": "2025-01-01",
        "author": [{"reference": "Practitioner/PRACT001"}],
        "content": [
            {
                "attachment": {
                    "contentType": "application/pdf",
                    "url": f"http://example.com/documents/{faker.uuid4()}.pdf",
                    "size": random.randint(1000, 5000),
                    "hash": faker.md5(),
                    "title": "Patient Outpatient Note",
                    "creation": "2025-01-01",
                }
            }
        ],
    }


def create_free_slot():
    """
    Creates a Slot resource.
    """
    return {
        "resourceType": "Slot",
        "id": "SLOT001",
        "serviceCategory": [{"text": "General Practice"}],
        "serviceType": [{"text": "Immunization"}],
        "specialty": [{"text": "Clinical immunology"}],
        "appointmentType": [{"text": "Walk-in"}],
        "schedule": {"reference": "Schedule/SCH001"},
        "status": "free",
        "start": "2025-04-25T09:15:00Z",
        "end": "2025-04-25T09:30:00Z",
    }


def create_busy_slot():
    """
    Creates a busy Slot resource.
    """
    return {
        "resourceType": "Slot",
        "id": "SLOT002",
        "serviceCategory": [{"text": "General Practice"}],
        "serviceType": [{"text": "Immunization"}],
        "specialty": [{"text": "Clinical immunology"}],
        "appointmentType": [{"text": "Walk-in"}],
        "schedule": {"reference": "Schedule/SCH001"},
        "status": "busy",
        "start": "2025-04-25T09:00:00Z",
        "end": "2025-04-25T09:15:00Z",
    }


def create_schedule():
    """
    Creates a Schedule resource.
    """
    return {
        "resourceType": "Schedule",
        "id": "SCH001",
        "active": True,
        "serviceCategory": [{"text": "General Practice"}],
        "serviceType": [{"text": "Immunization"}],
        "specialty": [{"text": "Clinical immunology"}],
        "actor": {"reference": "Practitioner/PRACT001"},
        "name": "John Smith - Immunization",
        "planningHorizon": {
            "start": "2025-04-25T08:00:00Z",
            "end": "2025-04-25T12:00:00Z",
        },
    }


def create_location():
    """
    Creates a Location resource.
    """
    return {
        "resourceType": "Location",
        "id": "LOC001",
        "name": "Main Clinic",
        "description": "Main clinic for general practice",
        "status": "active",
        "mode": "instance",
        "type": [{"text": "General Practice"}],
        "telecom": [{"system": "phone", "value": "+1-555-1234", "use": "work"}],
        "address": {
            "use": "work",
            "line": ["123 Main St"],
            "city": "Boston",
            "state": "MA",
            "postalCode": "02115",
        },
    }


def create_appointment(patient_id, practitioner_id, waitlist=False):
    """
    Creates an Appointment resource associated with a patient and practitioner.
    """
    return {
        "resourceType": "Appointment",
        "id": "APPT001",
        "status": "waitlist" if waitlist else "booked",
        "start": "2025-04-25T09:15:00Z",
        "end": "2025-04-25T09:30:00Z",
        "participant": [
            {"actor": {"reference": f"Patient/{patient_id}"}, "status": "accepted"},
            {
                "actor": {"reference": f"Practitioner/{practitioner_id}"},
                "status": "accepted",
            },
            {"actor": {"location": {"reference": "Location/LOC001"}}},
        ],
        "slot": [{"reference": "Slot/SLOT002"}],
    }


def post_to_fhir(resource):
    """
    Posts a FHIR resource to the FHIR server.
    """
    url = f"{FHIR_SERVER_URL}/{resource['resourceType']}"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    response = requests.post(url, json=resource, headers=headers)

    if response.status_code in [200, 201]:
        return response.json().get("id")
    else:
        raise ValueError(
            f"Failed to create {resource['resourceType']}: {response.text}"
        )


def upsert_to_fhir(resource):
    """
    Creates or updates a FHIR resource on the FHIR server with a specified ID.
    """
    url = f"{FHIR_SERVER_URL}/{resource['resourceType']}/{resource['id']}"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    response = requests.put(url, json=resource, headers=headers)

    if response.status_code in [200, 201]:
        logging.info(
            f"Successfully upserted {resource['resourceType']} with ID {resource['id']}"
        )
    else:
        logging.error(
            f"Failed to upsert {resource['resourceType']} with ID {resource['id']}: {response.status_code} {response.text}"
        )

def create_care_plan(patient_id):
    """
    Creates a CarePlan resource for surgeryassociated with a patient.
    """
    return {
        "resourceType": "CarePlan",
        "status": "active",
        "intent": "plan",
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "encounter": {
            "reference": f"Encounter/{encounter_id}"    
        }
    }

def populate_fhir():
    """
    Populates the FHIR server with sample resources.
    """
    # Delete existing resources
    delete_all_resources()

    # Create and post Organization
    organization = create_organization()
    upsert_to_fhir(organization)

    # Create and post Practitioner
    practitioner = create_practitioner()
    upsert_to_fhir(practitioner)

    # Create and post Location
    location = create_location()
    upsert_to_fhir(location)

    # Create and post Patient
    patient = create_patient()
    upsert_to_fhir(patient)

    # # Create and post RelatedPerson
    related_person = create_related_person(patient["id"])
    upsert_to_fhir(related_person)

    guanrtor = create_account(patient["id"])
    upsert_to_fhir(guanrtor)

    # Create and post Schedule
    schedule = create_schedule()
    upsert_to_fhir(schedule)

    # Create and post Slot
    free_slot = create_free_slot()
    upsert_to_fhir(free_slot)

    busy_slot = create_busy_slot()
    upsert_to_fhir(busy_slot)

    # Create and post Appointment
    appointment = create_appointment(patient["id"], practitioner["id"])
    upsert_to_fhir(appointment)

    # Create and post Condition
    condition = create_condition(patient["id"])
    upsert_to_fhir(condition)

    # Create and post Procedure
    procedure = create_procedure(patient["id"])
    upsert_to_fhir(procedure)

    # Create and post Coverage
    coverage = create_coverage(patient["id"])
    upsert_to_fhir(coverage)

    # Create and post Consent
    consent = create_consent(patient["id"])
    upsert_to_fhir(consent)

    # Create and post DocumentReference
    document_reference = create_document_reference(patient["id"])
    upsert_to_fhir(document_reference)


if __name__ == "__main__":
    populate_fhir()
