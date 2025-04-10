# This is for schedule agent testing purposes.

import requests
import random
from faker import Faker
import logging


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
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
    }

RESOURCE_TYPES =  ["Patient", "Condition", "Procedure", "Coverage", "Practitioner", "Organization", "RelatedPerson", "Consent", "DocumentReference", "Slot", "Schedule", "Appointment"]

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
    """Deletes a specific resource by ID."""
    url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
    response = requests.delete(url, headers=HEADERS)
    
    if response.status_code in [200, 204]:
        print(f"Deleted {resource_type}/{resource_id}")
    else:
        print(f"Failed to delete {resource_type}/{resource_id}: {response.text}")

def delete_all_resources():
    """Deletes all resources of the specified types."""
    for resource_type in RESOURCE_TYPES:
        print(f"Fetching {resource_type} resources...")
        resource_ids = get_resource_ids(resource_type)
        
        if not resource_ids:
            print(f"No {resource_type} resources found.")
            continue
        
        print(f"Deleting {len(resource_ids)} {resource_type} resources...")
        for resource_id in resource_ids:
            delete_resource(resource_type, resource_id)

def create_patient():
    """
    Creates a Patient resource with fake data.
    """
    return {
        "resourceType": "Patient",
        "id": "PAT001",
        "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
        "birthDate": "1990-06-15",
        "telecom": [{"system": "phone", "value": "123-456-7890"}],
        "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
    }

def create_condition(patient_id):
    """
    Creates a Condition resource associated with a patient.
    """
    return {
        "resourceType": "Condition",
        "id": "COND001",
        "code": {"text": "Hypertension"},
        "subject": {"reference": f"Patient/{patient_id}"}
    }

def create_procedure(patient_id):
    """
    Creates a Procedure resource associated with a patient.
    """
    return {
        "resourceType": "Procedure",
        "id": "PROC001",
        "status": "in-progress",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {"text": "Appendectomy"}
    }

def create_coverage(patient_id):
    """
    Creates a Coverage resource associated with a patient.
    """
    return {
        "resourceType": "Coverage",
        "id": "COV001",
        "status": "active",
        "kind": "insurance",
        "subscriber": {"reference": f"Patient/{patient_id}"},
        "beneficiary": {"reference": f"Patient/{patient_id}"},
        "insurer": {"reference": "Organization/ORG123"}
    }

def create_practitioner():
    """
    Creates a Practitioner resource with fake data.
    """
    return {
        "resourceType": "Practitioner",
        "id": "PRACT001",
        "name": [{"family": "Smith", "given": ["Jane"]}],
        "address" : [{
            "use" : "work",
            "line" : ["9 Main Ave"],
            "city" : "Boston",
            "state" : "MA",
            "postalCode" : "02115",
            "country" : "US"
        }],
        "gender": "female",
        "birthDate" : "1959-03-11",
        "communication" : [{ #TODO: fail to add speak english
            "language" : { "text" : "English" }
        }]
    }

def create_organization():
    """
    Creates an Organization resource.
    """
    return {
        "resourceType": "Organization",
        "id": "ORG001",
        "name": "XYZ Insurance"
    }

def create_related_person(patient_id):
    """
    Creates a RelatedPerson resource associated with a patient.
    """
    return {
        "resourceType": "RelatedPerson",
        "id": "REL001",
        "patient": {"reference": f"Patient/{patient_id}"},
        "relationship": [{"text": "Mother"}],
        "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
        "gender": "female",
        "birthDate": "1960-03-01"
    }

def create_consent(patient_id, document_id="DOC001"):
    """
    Creates a Consent resource associated with a patient.
    """
    return  {
        "resourceType" : "Consent",
        "id" : "CONSENT001",
        "status" : "active",
        "subject" : {
            "reference" : f"Patient/{patient_id}",
        },
        "date" : "2025-03-24",
        "controller" : [{
            "reference" : "Organization/ORG001"
        }],
        "sourceAttachment" : [{
            "title" : "The terms of the consent."
        }],
        "policyText": {
        "reference": f"DocumentReference/DOC001"}, #TODO: failed to add policy text
        "decision": "permit"
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
                    "display": "Outpatient Note"
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "date": "2025-01-01",
        "author": [
            {
                "reference": "Practitioner/PRACT001"
            }
        ],
        "content": [
            {
                "attachment": {
                    "contentType": "application/pdf",
                    "url": f"http://example.com/documents/{faker.uuid4()}.pdf",
                    "size": random.randint(1000, 5000),
                    "hash": faker.md5(),
                    "title": "Patient Outpatient Note",
                    "creation": "2025-01-01"
                }
            }
        ]
    }


def create_free_slot():
    """
    Creates a Slot resource.
    """
    return {
        "resourceType": "Slot",
        "id": "SLOT001",
        "serviceCategory": [{
            "text": "General Practice"
        }],
        "serviceType": [{
            "text": "Immunization"
        }],
        "specialty": [{
            "text": "Clinical immunology"
        }],
        "appointmentType": [{
            "text": "Walk-in"
        }],
        "schedule": {
            "reference": "Schedule/SCH001"
        },
        "status": "free",
        "start":  "2025-04-25T09:15:00Z",
        "end": "2025-04-25T09:30:00Z"
    }

def create_busy_slot():
    """
    Creates a busy Slot resource.
    """
    return {
        "resourceType": "Slot",
        "id": "SLOT002",
        "serviceCategory": [{
            "text": "General Practice"
        }],
        "serviceType": [{
            "text": "Immunization"
        }],
        "specialty": [{
            "text": "Clinical immunology"
        }],
        "appointmentType": [{
            "text": "Walk-in"
        }],
        "schedule": {
            "reference": "Schedule/SCH001"
        },
        "status": "busy",
        "start":  "2025-04-25T09:00:00Z",
        "end": "2025-04-25T09:15:00Z"
    }

def create_schedule():
    """
    Creates a Schedule resource.
    """
    return {
        "resourceType": "Schedule",
        "id": "SCH001",
        "active": True,
        "serviceCategory": [{
            "text": "General Practice"
        }],
        "serviceType": [{
            "text": "Immunization"
        }],
        "specialty": [{
            "text": "Clinical immunology"
        }],
        "actor": {
            "reference": "Practitioner/PRACT001"
        },
        "name": "John Smith - Immunization",
        "planningHorizon": {
            "start": "2025-04-25T08:00:00Z",
            "end": "2025-04-25T12:00:00Z"
        }
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
        "type": [{
            "text": "General Practice"
        }],
        "telecom": [{
            "system": "phone",
            "value": "+1-555-1234",
            "use": "work"
        }],
        "address": {
            "use": "work",
            "line": ["123 Main St"],
            "city": "Boston",
            "state": "MA",
            "postalCode": "02115"
        }
    }

def create_appointment(patient_id, practitioner_id):
    """
    Creates an Appointment resource associated with a patient and practitioner.
    """
    return {
        "resourceType": "Appointment",
        "id": "APPT001",
        "status": "booked",
        "start": "2025-04-25T09:15:00Z",
        "end": "2025-04-25T09:30:00Z",
        "participant": [
            {
                "actor": {
                    "reference": f"Patient/{patient_id}"
                },
                "status": "accepted"
            },
            {
                "actor": {
                    "reference": f"Practitioner/{practitioner_id}"
                },
                "status": "accepted"
            },
            {
                "actor": {
                    "location":{ "reference": "Location/LOC001" }
                }
            }
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
        "Accept": "application/fhir+json"
    }
    response = requests.post(url, json=resource, headers=headers)
    
    if response.status_code in [200, 201]:
        return response.json().get("id")
    else:
        raise ValueError(f"Failed to create {resource['resourceType']}: {response.text}")

def upsert_to_fhir(resource):
    """
    Creates or updates a FHIR resource on the FHIR server with a specified ID.
    """
    url = f"{FHIR_SERVER_URL}/{resource['resourceType']}/{resource['id']}"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    response = requests.put(url, json=resource, headers=headers)
    
    if response.status_code in [200, 201]:
        logging.info(f"Successfully upserted {resource['resourceType']} with ID {resource['id']}")
    else:
        logging.error(f"Failed to upsert {resource['resourceType']} with ID {resource['id']}: {response.status_code} {response.text}")

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
    related_person = create_related_person(patient['id'])
    upsert_to_fhir(related_person)

    # Create and post Schedule
    schedule = create_schedule()
    upsert_to_fhir(schedule)

    # Create and post Slot
    free_slot = create_free_slot()
    upsert_to_fhir(free_slot)

    busy_slot = create_busy_slot()
    upsert_to_fhir(busy_slot)

    # Create and post Appointment
    appointment = create_appointment(patient['id'], practitioner['id'])
    upsert_to_fhir(appointment)

    # Create and post Condition
    condition = create_condition(patient['id'])
    upsert_to_fhir(condition)

    # Create and post Procedure
    procedure = create_procedure(patient['id'])
    upsert_to_fhir(procedure)

    # Create and post Coverage
    coverage = create_coverage(patient['id'])
    upsert_to_fhir(coverage)

    # Create and post Consent
    consent = create_consent(patient['id'])
    upsert_to_fhir(consent)

    # Create and post DocumentReference
    document_reference = create_document_reference(patient['id'])
    upsert_to_fhir(document_reference)
    

if __name__ == "__main__":
    populate_fhir()