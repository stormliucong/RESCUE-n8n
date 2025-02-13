import requests
import json
from datetime import datetime

import base64

# Your credentials
username = "f54370de-eaf3-4d81-a17e-24860f667912"
password = "75d8e7d06bf9283926c51d5f461295ccf0b69128e983b6ecdd5a9c07506895de"

# Encode credentials
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()


# Base URL for your FHIR server
FHIR_BASE = "http://localhost:8103/fhir/R4"
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json",
    "Authorization": f"Basic {encoded_credentials}"
}

def create_provider(full_name, family, given):
    """
    Create a Practitioner (provider) resource on the FHIR server.
    """
    provider_data = {
        "resourceType": "Practitioner",
        "name": [{
            "family": family,
            "given": [given],
            "text": full_name
        }]
    }
    response = requests.post(f"{FHIR_BASE}/Practitioner", headers=HEADERS, data=json.dumps(provider_data))
    if response.status_code in (200, 201):
        provider = response.json()
        provider_id = provider.get("id")
        print(f"Created Practitioner '{full_name}' with ID: {provider_id}")
        return provider_id
    else:
        print(f"Error creating Practitioner '{full_name}':", response.text)
        return None

def create_patient(family, given):
    """
    Create a Patient resource on the FHIR server.
    """
    patient_data = {
        "resourceType": "Patient",
        "name": [{
            "family": family,
            "given": [given]
        }]
    }
    response = requests.post(f"{FHIR_BASE}/Patient", headers=HEADERS, data=json.dumps(patient_data))
    if response.status_code in (200, 201):
        patient = response.json()
        patient_id = patient.get("id")
        print(f"Created Patient '{given} {family}' with ID: {patient_id}")
        return patient_id
    else:
        print(f"Error creating Patient '{given} {family}':", response.text)
        return None

def create_genetic_test_order(provider_id, patient_id):
    """
    Create a ServiceRequest resource representing a genetic test order.
    The order references the patient and the provider (as the requester).
    """
    order_data = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/service-category",
                "code": "laboratory"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "69548-7",   # Example LOINC code for a genetic test (adjust if needed)
                "display": "Genetic test"
            }]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "authoredOn": datetime.now().strftime("%Y-%m-%d"),
        "requester": {
            "reference": f"Practitioner/{provider_id}"
        }
    }
    response = requests.post(f"{FHIR_BASE}/ServiceRequest", headers=HEADERS, data=json.dumps(order_data))
    if response.status_code in (200, 201):
        order = response.json()
        order_id = order.get("id")
        print(f"Created ServiceRequest (genetic test order) with ID: {order_id} for Patient/{patient_id} ordered by Practitioner/{provider_id}")
        return order_id
    else:
        print(f"Error creating ServiceRequest for Patient/{patient_id}:", response.text)
        return None

def main():
    # Create three providers (Practitioners)
    providers = []
    providers.append(create_provider("Dr. Alice Smith", family="Ordertest", given="Alice"))
    providers.append(create_provider("Dr. Bob Jones", family="Ordertest", given="Bob"))
    providers.append(create_provider("Dr. Charlie Brown", family="Ordertest", given="Charlie"))
    
    # Create three patients
    patients = []
    patients.append(create_patient(family="Ordertest", given="John"))
    patients.append(create_patient(family="Ordertest", given="Jane"))
    patients.append(create_patient(family="Ordertest", given="Jim"))
    
    # Create a genetic test order (ServiceRequest) for each patient using the corresponding provider
    for provider_id, patient_id in zip(providers, patients):
        if provider_id and patient_id:
            create_genetic_test_order(provider_id, patient_id)
        else:
            print("Skipping order creation due to missing provider or patient ID.")

if __name__ == '__main__':
    main()
