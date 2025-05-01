# task_01_enter_new_patient.py
import os
import requests # type: ignore
import json
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult
from dataclasses import asdict
from dotenv import load_dotenv 



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

    def execute_human_agent(self) -> ExecutionResult:
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

        response = self.post_to_fhir(payload)
        response_msg = None
        if response.status_code == 201:
            response_msg = f'Patient "John Doe" created successfully with ID: {response.json()["id"]}'
        else:
            response_msg = f'Failed to create patient: {response.status_code} {response.text}'
        
        execution_result = ExecutionResult(
            execution_success=response.status_code == 201,
            response_msg=response_msg,
        )
        return execution_result

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:

            # Validate the patient resources
            params = {
                "family": "Doe",
                "given": "John"
            }
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Patient",
                headers=self.HEADERS,
                params=params
            )
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            response_json = response.json()
            assert 'entry' in response_json, "No patient found"
            assert len(response_json['entry']) > 0, "No patient found"
            patient = response_json['entry'][0]['resource']
            assert patient['name'][0]['family'] == "Doe", f"Expected family name 'Doe', got {patient['name'][0]['family']}"
            assert patient['name'][0]['given'][0] == "John", f"Expected given name 'John', got {patient['name'][0]['given'][0]}"
            assert patient['birthDate'] == "1990-06-15", f"Expected birth date '1990-06-15', got {patient['birthDate']}"
            # Check if the patient is created successfully

            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=True,
                assertion_error_message=None,
            )

        except AssertionError as e:
            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=str(e),
            )
        except Exception as e:
            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=f"Unexpected error: {str(e)}",
            )
            

if __name__ == "__main__":
    load_dotenv()
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")
    HEADERS = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    
    task = EnterNewPatientTask(FHIR_SERVER_URL, N8N_URL, N8N_EXECUTION_URL)
   
    # task.cleanup_test_data()
    # task.prepare_test_data()
    # human_response = task.execute_human_agent()
    # eval_results = task.validate_response(human_response)
    # print(f'Human response: {eval_results}')
    task.cleanup_test_data()
    task.prepare_test_data()
    n8n_execution_log = task.execute_n8n_agent()
    print("N8N RESPONSE TASK")
    print(n8n_execution_log.tool_calls['createResource'])
    print("EVAL TASK")
    eval_results = task.validate_response(n8n_execution_log)
    print(f'Eval response: TaskResult {eval_results}')
    # save ExecutionResult object to a json file
    with open("n8n_response.json", "w") as f:
        json.dump(asdict(eval_results), f, indent=4)
    
    
