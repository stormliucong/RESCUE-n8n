# eval/scheduler/task_04b_search_nonexistent_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonexistentMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "4b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Medical History"

    def get_prompt(self) -> str:
        return """
Task: Search for patient medical history

Search for the existing patient id=PAT002 to see if he has any medical history.
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient without any conditions
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "subject": "Patient/PAT002"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Condition",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for medical history: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {response_json.get('total', 0)} medical condition(s) for patient PAT002"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify no medical history was found
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Condition",
                headers=self.HEADERS,
                params={"subject": "Patient/PAT002"}
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, f"Expected no medical history, but got {response_json['total']}"
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
