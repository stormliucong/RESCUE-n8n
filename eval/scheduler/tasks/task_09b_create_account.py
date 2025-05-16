# task_09b_create_account.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class CreateAccountTask(TaskInterface):
    def get_task_id(self) -> str:
        return "9b"

    def get_task_name(self) -> str:
        return "Create Account"

    def get_prompt(self) -> str:
        return """
Task: Create an account resource

Create an account resource for the patient PAT001.

After creation, return the new Account ID using the following format: <ACCOUNT>account_id</ACCOUNT>
"""

    def prepare_test_data(self) -> None:
        try:
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "2010-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")



    def execute_human_agent(self) -> ExecutionResult:
        account_payload = {
            "resourceType": "Account",
            "status": "active",
            "subject": {"reference": "Patient/PAT001"}
        }
        
        response = requests.post(
            f"{self.FHIR_SERVER_URL}/Account",
            headers=self.HEADERS,
            json=account_payload
        )
        
        if response.status_code != 201:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to create account: {response.text}"
            )

        response_json = response.json()
        account_id = response_json.get('id')
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Created account with ID <ACCOUNT>{account_id}</ACCOUNT>"
        )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the account was created correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Account",
                headers=self.HEADERS,
                params={"subject": "Patient/PAT001"}
            )
            
            assert response.status_code in [200, 201], f"Expected status code 200 or 201, got {response.status_code}"
            
            response_json = response.json()
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one account"
            
            account = response_json['entry'][0]['resource']
            assert account["resourceType"] == "Account", "Invalid resource type"

            # Structured-output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<ACCOUNT>" in response_msg, "Expected to find <ACCOUNT> tag"
            assert "</ACCOUNT>" in response_msg, "Expected to find </ACCOUNT> tag"
            account_id = response_msg.split("<ACCOUNT>")[1].split("</ACCOUNT>")[0]
            assert account_id is not None, "Expected to find account_id"
            
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
            {"createResource": 0},
            {"getResourceById": 0, "updateResource": 1},
            {"getAllResources": 0, "createResource": 1},
            {"getAllResources": 0, "deleteResource": 1, "createResource": 2}
        ]

    def get_required_resource_types(self) -> list:
        return ["Account"]

    def get_prohibited_tools(self) -> list:
        return []

    def get_difficulty_level(self) -> int:
        return 1
