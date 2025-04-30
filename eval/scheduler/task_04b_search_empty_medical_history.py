# eval/scheduler/task_04b_search_nonexistent_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class SearchNonexistentMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "4b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Medical History"

    def get_prompt(self) -> str:
        return """
Task: Search for patient medical history

Search for the existing patient id=PAT002 to see if he has any medical history.
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient without any conditions
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        params = {
            "subject": "Patient/PAT002"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Condition",
            headers=self.HEADERS,
            params=params
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, f"Expected no medical history, but got {response_json['total']}"
            assert 'entry' not in response_json, "Expected no entries in the response"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "conditions_found": 0,
                    "message": "No medical history found for patient PAT002"
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
    
    task = SearchNonexistentMedicalHistoryTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)