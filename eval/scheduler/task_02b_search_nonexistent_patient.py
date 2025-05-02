# task_02b_search_nonexistent_patient.py

import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonexistentPatientTask(TaskInterface):
    def get_task_id(self) -> str:
        return "2b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Patient"

    def get_prompt(self) -> str:
        return """
                Task: Search for a nonexistent patient

                Search the database for the following patient:
                - Full Name: John Doe
                - Birth Date: June 15, 1991

                If the patient exists, return their Patient resource ID.
                If the patient doesn't exist, classify them as a new patient.
                """

    def prepare_test_data(self) -> None:
        try:
            # Clean up existing resources
            self.delete_all_resources()
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        search_params = {
            "family": "Doe",
            "given": "John",
            "birthdate": "1991-06-15"
        }
        
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Patient",
            headers=self.HEADERS,
            params=search_params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for patient: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {response_json.get('total', 0)} patient(s) matching the criteria"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify no patient was found
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Patient",
                headers=self.HEADERS,
                params={
                    "family": "Doe",
                    "given": "John",
                    "birthdate": "1991-06-15"
                }
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, "Expected to find no patient"
            assert 'entry' not in response_json or len(response_json['entry']) == 0, "Expected no entries in the response"

            return TaskResult(
                task_success=True,
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result
            )

        except AssertionError as e:
            return TaskResult(
                task_success=False,
                assertion_error_message=str(e),
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result
            )
        except Exception as e:
            return TaskResult(
                task_success=False,
                assertion_error_message=f"Unexpected error: {str(e)}",
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result
            )

    def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
        # This method will be implemented with detailed failure mode analysis later
        return TaskFailureMode(
            incorrect_tool_selection=False,
            incorrect_tool_order=False,
            incorrect_resource_type=False,
            error_codes=None
        )
            