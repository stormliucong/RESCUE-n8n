# eval/scheduler/task_04a_search_existing_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class SearchExistingMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "4a"

    def get_task_name(self) -> str:
        return "Search Existing Medical History"

    def get_prompt(self) -> str:
        return """
Task: Search for patient medical history

Search for the existing patient id=PAT001 to see if he has any medical history.
"""

    def prepare_test_data(self) -> None:
        try:
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
            # Create condition for the patient
            condition_data = {
                "resourceType": "Condition",
                "id": "Appendicitis001",
                "subject": { "reference": "Patient/PAT001" },
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "74400008",
                        "display": "Appendicitis"
                    }],
                    "text": "Appendicitis"
                },
                "clinicalStatus": { "coding": [{ "code": "active" }] }
            }
            self.upsert_to_fhir(condition_data)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        params = {
            "subject": "Patient/PAT001"
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
            assert response_json['total'] > 0, f"Expected to find at least one medical history, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, f"Expected to find at least one medical history, but got {len(response_json['entry'])}"

            # Validate the condition details
            condition = response_json['entry'][0]['resource']
            assert condition['resourceType'] == "Condition", "Resource type must be Condition"
            assert condition['subject']['reference'] == "Patient/PAT001", "Subject reference must be Patient/PAT001"
            
            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "conditions_found": response_json['total'],
                    "conditions": [entry['resource'] for entry in response_json['entry']]
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
    
    task = SearchExistingMedicalHistoryTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)