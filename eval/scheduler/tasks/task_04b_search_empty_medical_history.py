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

If found, return the condition's ID using the following format: <CONDITION>condition_id</CONDITION>

If not, return this exact sentence: "No medical history found"
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
            response_msg=f"Found {response_json.get('total', 0)} medical condition(s) for patient PAT002 : No medical history found"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            
            # Additional assertions (to be discussed)
            response_msg = execution_result.response_msg
            assert "no medical history found" in response_msg.lower(), "Expected response message to indicate no medical history found; got {response_msg}"

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

    def get_required_tool_call_sets(self) -> list:
        return [
            {"getAllResources": 0},
            {"getResourceById": 0}
        ]

    def get_required_resource_types(self) -> list:
        return ["Condition"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 1
