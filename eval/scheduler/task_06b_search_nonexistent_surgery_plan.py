# task_06b_search_nonexistent_surgery_plan.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class SearchNonexistentSurgeryPlanTask(TaskInterface):
    def get_task_id(self) -> str:
        return "6b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Surgery Plan"

    def get_prompt(self) -> str:
        return """
Task: Search for surgery plan

Search and find if patient id=PAT002 has any surgery plan two weeks from now.
"""

    def prepare_test_data(self) -> None:
        try:
            today = datetime.today().date()
            three_weeks_later = today + timedelta(days=21)

            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "1991-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)

            # Create service request for three weeks later (outside search window)
            service_request = {
                "resourceType": "ServiceRequest",
                "id": "APPENDECTOMY-REQUEST-002",
                "status": "active",
                "intent": "order",
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "80146002",
                        "display": "Appendectomy (procedure)"
                    }],
                    "text": "Appendectomy"
                },
                "subject": {
                    "reference": "Patient/PAT002"
                },
                "occurrenceDateTime": three_weeks_later.strftime("%Y-%m-%d")
            }
            self.upsert_to_fhir(service_request)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        today = datetime.today().date()
        two_weeks_later = today + timedelta(days=14)

        params = {
            "subject": "Patient/PAT002",
            "occurrence": [
                f"ge{today.isoformat()}",
                f"le{two_weeks_later.isoformat()}"
            ]
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/ServiceRequest",
            headers=self.HEADERS,
            params=params
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, f"Expected no surgery plans, but got {response_json['total']}"
            assert 'entry' not in response_json, "Expected no entries in the response"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "plans_found": 0,
                    "message": "No surgery plans found within two weeks for patient PAT002"
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
    
    task = SearchNonexistentSurgeryPlanTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)