# task_02a_search_existing_patient.py

import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class SearchExistingPatientTask(TaskInterface):
    def get_task_id(self) -> str:
        return "2a"

    def get_task_name(self) -> str:
        return "Search Existing Patient"

    def get_prompt(self) -> str:
        return """
                Task: Search for an existing patient

                Search the database for the following patient:
                - Full Name: John Doe
                - Birth Date: June 15, 1990

                If the patient exists, return their Patient resource ID.
                If the patient doesn't exist, classify them as a new patient.
                """

    def prepare_test_data(self) -> None:
        try:
            # Clean up existing resources
            self.delete_all_resources()

            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        search_params = {
            "family": "Doe",
            "given": "John",
            "birthdate": "1990-06-15"
        }
        
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Patient",
            headers=self.HEADERS,
            params=search_params
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one patient"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one patient"
            assert 'id' in response_json['entry'][0]['resource'], "Expected to find id in the response"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "exists": True,
                    "id": response_json['entry'][0]['resource']['id']
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
    from dotenv import load_dotenv # type: ignore
    load_dotenv()
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    HEADERS = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }

    task = SearchExistingPatientTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)