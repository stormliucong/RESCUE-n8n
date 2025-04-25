# task_09c_add_guarantor.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class AddGuarantorTask(TaskInterface):
    def get_task_id(self) -> str:
        return "9c"

    def get_task_name(self) -> str:
        return "Add Guarantor"

    def get_prompt(self) -> str:
        return """
Task: Add guarantor to account

Add the guarantor responsible for patient PAT001's billing:
- Guarantor: Alice Doe (mother)
"""

    def prepare_test_data(self) -> None:
        try:
            # Create patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "2010-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)

            # Create related person
            related_person_resource = {
                "resourceType": "RelatedPerson",
                "id": "REL001",
                "patient": {"reference": "Patient/PAT001"},
                "relationship": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "MOTHER"
                    }],
                    "text": "mother"
                }],
                "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
                "birthDate": "1960-03-01"
            }
            self.upsert_to_fhir(related_person_resource)

            # Create initial account
            account_payload = {
                "resourceType": "Account",
                "id": "ACC001",
                "status": "active",
                "subject": {"reference": "Patient/PAT001"}
            }
            response = requests.post(
                f"{self.FHIR_SERVER_URL}/Account",
                headers=self.HEADERS,
                json=account_payload
            )
            if response.status_code != 201:
                raise Exception("Failed to create initial account")

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        update_payload = {
            "resourceType": "Account",
            "id": "ACC001",
            "status": "active",
            "subject": {"reference": "Patient/PAT001"},
            "guarantor": [{
                "party": {"reference": "RelatedPerson/REL001"}
            }]
        }
        
        response = requests.put(
            f"{self.FHIR_SERVER_URL}/Account/ACC001",
            headers=self.HEADERS,
            json=update_payload
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code in [200, 201], f"Expected status code 200/201, got {response.status_code}"
            
            response_json = response.json()
            assert response_json["resourceType"] == "Account", "Invalid resource type"
            assert response_json["status"] == "active", "Account status should be active"
            assert "guarantor" in response_json, "Guarantor not added to account"
            assert response_json["guarantor"][0]["party"]["reference"] == "RelatedPerson/REL001", "Invalid guarantor reference"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "account_id": response_json["id"],
                    "guarantor_reference": response_json["guarantor"][0]["party"]["reference"]
                }
            )

        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response.json() if hasattr(response, 'json') else None
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_data=response.json() if hasattr(response, 'json') else None
            )

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = AddGuarantorTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
