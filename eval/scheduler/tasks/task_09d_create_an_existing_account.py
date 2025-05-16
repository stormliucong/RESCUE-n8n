# task_09d_create_an_existing_account.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class CreateExistingAccountTask(TaskInterface):
    def get_task_id(self) -> str:
        return "9d"

    def get_task_name(self) -> str:
        return "Create Account for Existing Patient"

    def get_prompt(self) -> str:
        return """
Task: Create an account resource for an existing patient PAT001

Create an account resource for the patient PAT001. 
If the account for given patient is already created, Return "There is already an account for this patient <ACCOUNT>account_id</ACCOUNT>"

"""

    def prepare_test_data(self) -> None:
        
        patient_resource = {
            "resourceType": "Patient",
            "id": "PAT001",
            "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
            "birthDate": "2010-06-15",
            "telecom": [{"system": "phone", "value": "123-456-7890"}],
            "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
        }
        self.upsert_to_fhir(patient_resource)
        
        account_resource = {
            "resourceType": "Account",
            "id": "ACC001",
            "status": "active",
            "subject": {"reference": "Patient/PAT001"}
        }
        self.upsert_to_fhir(account_resource)

    def execute_human_agent(self) -> ExecutionResult:
        # First verify the patient exists
        patient_response = requests.get(
            f"{self.FHIR_SERVER_URL}/Patient/PAT001",
            headers=self.HEADERS
        )
        
        if patient_response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Patient PAT001 not found: {patient_response.text}"
            )

        # Second check if the account already exists
        account_response = requests.get(
            f"{self.FHIR_SERVER_URL}/Account",
            headers=self.HEADERS,
            params={"subject": "Patient/PAT001"}
        )
        
        if account_response.status_code in [200, 201]:
            account_json = account_response.json()
            account_id = account_json['entry'][0]['resource']['id']
            return ExecutionResult(
                execution_success=True,
                response_msg=f"There is already an account for this patient <ACCOUNT>{account_id}</ACCOUNT>"
            )
        
        else:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to get an account for this patient"
            )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the patient exists
            response_msg = response_msg.strip()
            assert "<ACCOUNT>" in response_msg, "Expected to find <ACCOUNT> tag"
            assert "</ACCOUNT>" in response_msg, "Expected to find </ACCOUNT> tag"
            account_id = response_msg.split("<ACCOUNT>")[1].split("</ACCOUNT>")[0]
            assert account_id is not None, "Expected to find account_id"
            expected_id = self.execute_human_agent().response_msg.split("<ACCOUNT>")[1].split("</ACCOUNT>")[0]
            assert account_id == expected_id, f"Expected account_id {expected_id}, got {account_id}"

            # Verify the account was not created
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Account",
                headers=self.HEADERS,
                params={"subject": "Patient/PAT001"}
            )
            assert response.status_code in [200, 201], f"Expected status code 200 or 201, got {response.status_code}"
            
            response_json = response.json()
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) == 1, "Expected to find only one account"
            account_id = response_json['entry'][0]['resource']['id']
            assert account_id == "ACC001", f"Expected account_id ACC001, got {account_id}"
            
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
