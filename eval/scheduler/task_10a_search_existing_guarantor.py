# task_10a_search_existing_guarantor.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult


class SearchExistingGuarantorTask(TaskInterface):
    def get_task_id(self) -> str:
        return "10a"

    def get_task_name(self) -> str:
        return "Search Existing Guarantor"

    def get_prompt(self) -> str:
        return """
Task: Search for patient's guarantor

Identify and confirm the guarantor responsible for this patient's insurance policy.
Patient's details:
- Name: John Doe
- ID: PAT001
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
                "relationship": [{"text": "mother"}],
                "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
                "gender": "female",
                "birthDate": "1960-03-01"
            }
            self.upsert_to_fhir(related_person_resource)

            # Create account with guarantor
            account_resource = {
                "resourceType": "Account",
                "id": "ACC001",
                "status": "active",
                "subject": {"reference": "Patient/PAT001"},
                "guarantor": [{"party": {"reference": "RelatedPerson/REL001"}}]
            }
            self.upsert_to_fhir(account_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        params = {
            "patient": "Patient/PAT001"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Account",
            headers=self.HEADERS,
            params=params
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one guarantor"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one account"
            
            account = response_json['entry'][0]['resource']
            assert 'guarantor' in account, "No guarantor found in account"
            guarantor_reference = account['guarantor'][0]['party']['reference']
            assert guarantor_reference == "RelatedPerson/REL001", "Invalid guarantor reference"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "account_id": account.get("id"),
                    "guarantor_reference": guarantor_reference
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
    
    task = SearchExistingGuarantorTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)