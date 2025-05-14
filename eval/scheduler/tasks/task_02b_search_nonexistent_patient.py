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

                If the patient exists, return their Patient resource ID using the following format:                    
                 
                <patient_id>PATIENTID</patient_id>
                
                If the patient doesn't exist, return this exact sentence: "This is a new patient"
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
        if "entry" in response_json and len(response_json["entry"]) > 0:
            # Patient found
            patient_id = response_json["entry"][0]["resource"]["id"]
            return ExecutionResult(
                execution_success=True,
                response_msg=f"<patient_id>{patient_id}</patient_id>"
            )
        # No patient found
        return ExecutionResult(
            execution_success=True,
            response_msg=f"This is a new patient"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            assert "new patient" in response_msg.lower(), f"Expected 'This is a new patient', got '{response_msg}'"

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

    # def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
    #     # This method will be implemented with detailed failure mode analysis later
    #     return TaskFailureMode(
    #         incorrect_tool_selection=False,
    #         incorrect_tool_order=False,
    #         incorrect_resource_type=False,
    #         error_codes=None
    #     )
            