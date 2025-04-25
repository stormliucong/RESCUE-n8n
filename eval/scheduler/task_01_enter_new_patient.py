"""
Evaluation Prompt:
1.
A new patient needs to be registered. Please enter the following details into the system:
 - Name: John Doe
 - Date of Birth: 1990-06-15
 - Phone: (123) 456-7890
 - Address: 123 Main St, Boston, MA
"""
import os
import requests # type: ignore
import json
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class EnterNewPatientTask(TaskInterface):
    def get_task_id(self) -> str:
        return "1"

    def get_task_name(self) -> str:
        return "Enter New Patient"

    def get_prompt(self) -> str:
        return """
                Task: Create a new patient record

                You need to create a new patient with the following information:
                - Full Name: John Doe
                - Birth Date: June 15, 1990
                - Phone Number: (123) 456-7890
                - Address: 123 Main St, Boston, MA

                """

    def prepare_test_data(self) -> None:
        # Check if FHIR server is accessible
        try:
            response = requests.get(f"{self.FHIR_SERVER_URL}/metadata", headers=self.HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"FHIR server is not accessible: {str(e)}")

    def execute_human_agent(self) -> Dict:
        payload = {
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": "Doe",
                    "given": ["John"]
                }
            ],
            "birthDate": "1990-06-15",
            "telecom": [
                {
                    "system": "phone",
                    "value": "(123) 456-7890"
                }
            ],
            "address": [
                {
                    "line": ["123 Main St"],
                    "city": "Boston",
                    "state": "MA"
                }
            ]
        }

        response = requests.post(
            f"{self.FHIR_SERVER_URL}/Patient",
            headers=self.HEADERS,
            json=payload
        )

        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:

            # Validate response status
            assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"

            # Validate response content
            response_json = response.json()
            assert response_json.get("resourceType") == "Patient", "Resource type must be Patient"
            

            return TaskResult(
                success=True,
                error_message=None,
                response_data=response_json
            )

        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response_json
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_data=response_json
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
    
    task = EnterNewPatientTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    # human_response = task.execute_human_agent()
    # eval_results = task.validate_response(human_response)
    # print(eval_results)
    n8n_response = task.execute_n8n_agent()
    print(n8n_response)
