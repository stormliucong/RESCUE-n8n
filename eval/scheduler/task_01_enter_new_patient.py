# task_01_enter_new_patient.py
import os
import requests # type: ignore
import json
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode
from dataclasses import asdict
from dotenv import load_dotenv
import re



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
            


    def identify_failure_mode(self, taskResult: TaskResult) -> TaskFailureMode:
        # Initialising the failure mode objcet
        failure_mode = TaskFailureMode()

        # No failure if task succeeded
        if taskResult.task_success:
            return failure_mode  # All fields default to False / None
        
        # n8n workflow execution success
        exec_result = taskResult.execution_result
        if not exec_result:
            failure_mode.critical_error = True
            return failure_mode
        
        # Detect specific error codes from tool outputs
        error_codes = []
        if exec_result.tool_calls:
            for calls in exec_result.tool_calls.values():
                for call in calls:
                    out = call.get("output")
                    if isinstance(out, str) and "error" in out.lower():
                        if "status code" in out:
                            # Extract status code from message
                            parts = out.split("status code")
                            if len(parts) > 1:
                                code = parts[1].split()[0]
                                error_codes.append(code)
        if error_codes:
            failure_mode.error_codes = error_codes
