# task_10b_search_nonexistent_guarantor.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonexistentGuarantorTask(TaskInterface):
    def get_task_id(self) -> str:
        return "10b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Guarantor"

    def get_prompt(self) -> str:
        return """
Task: Search for patient's guarantor

Identify and confirm the guarantor responsible for this patient's insurance policy.
Patient's details:
- Name: Jane Doe
- ID: PAT002

If found, return the guarantor’s ID using the following format: <GUARANTOR>guarantor_id</GUARANTOR>
If none found, return the exact sentence: "No guarantor found for patient PAT002"
"""

    def prepare_test_data(self) -> None:
        try:
            # Create patient without any account or guarantor
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
            "patient": "Patient/PAT002"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Account",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search account: {response.text}"
            )

        response_json = response.json()
        if response_json.get('total', 0) > 0:
            guarantor_reference = response_json['entry'][0]['resource']['guarantor'][0]['party']['reference']
            guarantor_id = guarantor_reference.split('/')[-1]
            return ExecutionResult(
                execution_success=True,
                response_msg=f"Found guarantor {guarantor_reference} for patient PAT002: <GUARANTOR>{guarantor_id}</GUARANTOR>"
            )
        else:
            return ExecutionResult(
                execution_success=True,
                response_msg="No guarantor found for patient PAT002"
            )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            
            # Structured-output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "no guarantor found" in response_msg.lower(), f"Expected 'No guarantor found for patient PAT002', got '{response_msg}'"

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

    def get_required_tool_call_sets(self) -> list:
        return [
            {"getAllResources": 0},
            {"getResourceById": 0}
        ]

    def get_required_resource_types(self) -> list:
        return ["Account"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 1
