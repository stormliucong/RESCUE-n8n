from abc import ABC, abstractmethod
import time
from typing import Dict, Any, Optional
import requests # type: ignore
from dataclasses import dataclass

@dataclass
class TaskResult:
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    metrics: Optional[Dict] = None

class TaskInterface(ABC):
    def __init__(self, fhir_server_url, n8n_url):
        self.FHIR_SERVER_URL = fhir_server_url
        self.HEADERS = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
        self.N8N_AGENT_URL = n8n_url
        self.RESOURCE_TYPES = [
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
        
    def get_resource_ids(self, resource_type):
        """Fetches all resource IDs for the given resource type, handling pagination."""
        url = f"{self.FHIR_SERVER_URL}/{resource_type}?_count=1000"
        resource_ids = []
        while url:
            response = requests.get(url, headers=self.HEADERS)
            if response.status_code != 200:
                print(f"Failed to fetch {resource_type}: {response.status_code}")
                break
            
            data = response.json()
            if "entry" in data:
                resource_ids.extend([entry["resource"]["id"] for entry in data["entry"]])

            # Find the next page URL
            next_url = None
            if "link" in data:
                for link in data["link"]:
                    if link["relation"] == "next":
                        next_url = link["url"]
                        break

            url = next_url  # continue if next page exists, else break the loop
        return resource_ids
        
    def delete_resource(self, resource_type, resource_id):
        """Deletes a specific resource by ID, removing any references to it first."""
           
        # Now delete the resource
        url = f"{self.FHIR_SERVER_URL}/{resource_type}/{resource_id}"
        response = requests.delete(url, headers=self.HEADERS)

        if response.status_code in [200, 204]:
            print(f"Deleted {resource_type}/{resource_id}")
        else:
            print(f"Failed to delete {resource_type}/{resource_id}: {response.text}")
        
    def delete_all_resources(self):
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
            resource_ids = self.get_resource_ids(resource_type)

            if not resource_ids:
                print(f"No {resource_type} resources found.")
                continue

            print(f"Deleting {len(resource_ids)} {resource_type} resources...")
            for resource_id in resource_ids:
                self.delete_resource(resource_type, resource_id)
                # Add a small delay to prevent overwhelming the server
                time.sleep(0.1)
    
    def post_to_fhir(self,resource):
        """
        Posts a FHIR resource to the FHIR server.
        """
        url = f"{self.FHIR_SERVER_URL}/{resource['resourceType']}"
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

    def upsert_to_fhir(self,resource):
        """
        Creates or updates a FHIR resource on the FHIR server with a specified ID.
        """
        url = f"{self.FHIR_SERVER_URL}/{resource['resourceType']}/{resource['id']}"
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }
        response = requests.put(url, json=resource, headers=headers)

        if response.status_code in [200, 201]:
            print(
                f"Successfully upserted {resource['resourceType']} with ID {resource['id']}"
            )
        else:
            print(
                f"Failed to upsert {resource['resourceType']} with ID {resource['id']}: {response.status_code} {response.text}"
            )
            
    @abstractmethod
    def get_task_id(self) -> str:
        """Return the task ID"""
        pass

    @abstractmethod
    def get_task_name(self) -> str:
        """Return the task name"""
        pass
    @abstractmethod
    def get_prompt(self) -> str:
        """Return the prompt for the task"""
        pass

    @abstractmethod
    def prepare_test_data(self) -> None:
        """Prepare any necessary FHIR resources for the test"""
        pass

    def cleanup_test_data(self) -> None:
        """Clean up any test data created during the test"""
        self.delete_all_resources()
        
    def execute_n8n_agent(self) -> TaskResult:
        """Execute the task on n8n workflowand and return results"""
        prompt = self.get_prompt()
        print(prompt)
        payload = {
            "prompt": prompt,
            "fhir_server_url": self.FHIR_SERVER_URL
        }
        response = requests.post(self.N8N_AGENT_URL, json=payload)
        return response.json()
        
    @abstractmethod
    def execute_human_agent(self) -> TaskResult:
        """Execute the expected actions that a human should perform"""
        pass
    
    @abstractmethod
    def validate_response(self, response_data: Any) -> TaskResult:
        """Validate the response using assertions"""
        pass
