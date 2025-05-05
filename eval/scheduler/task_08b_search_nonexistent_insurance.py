# task_08b_search_nonexistent_insurance.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonexistentInsuranceTask(TaskInterface):
    def get_task_id(self) -> str:
        return "8b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Insurance"

    def get_prompt(self) -> str:
        return """
Task: Search for patient insurance information

Search if patient insurance information has been entered in the system for:
- Beneficiary: Jane Doe (id=PAT002)
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient without insurance
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "2020-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "beneficiary": "Patient/PAT002",
            "status": "active"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Coverage",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for insurance: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {response_json.get('total', 0)} insurance coverage(s) for patient PAT002"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify no insurance coverage exists for the patient
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Coverage",
                headers=self.HEADERS,
                params={"beneficiary": "Patient/PAT002", "status": "active"}
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, f"Expected no insurance, but got {response_json['total']}"
            assert 'entry' not in response_json, "Expected no entries in the response"

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