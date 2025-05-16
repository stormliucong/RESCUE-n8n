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
Task: Search for patient (PAT002) insurance information

Search if patient insurance information has been entered in the system for:
- Beneficiary: Jane Doe (id=PAT002)

If found, return the coverage ID using the following format: <COVERAGE>coverage_id</COVERAGE>
If none found, return the exact sentence: No insurance coverage found
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
        # added logic
        response_json = response.json()
        if response_json.get('total', 0) > 0:
            coverage_id = response_json['entry'][0]['resource']['id']
            return ExecutionResult(
                execution_success=True,
                response_msg=f"Found {response_json['total']} insurance coverage(s) for patient PAT002: <COVERAGE>{coverage_id}</COVERAGE>"
            )
        else:
            return ExecutionResult(
                execution_success=True,
                response_msg="No insurance coverage found"
            )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Structured-output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            assert "no insurance coverage found" in response_msg.lower(), f"Expected 'No insurance coverage found', got '{response_msg}'"

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

    def get_required_tool_call_sets(self) -> list:
        return [
            {"getAllResources": 0},
            {"getResourceById": 0}
        ]

    def get_required_resource_types(self) -> list:
        return ["Coverage"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 1

    # def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
    #     # This method will be implemented with detailed failure mode analysis later
    #     return TaskFailureMode(
    #         incorrect_tool_selection=False,
    #         incorrect_tool_order=False,
    #         incorrect_resource_type=False,
    #         error_codes=None
    #     )