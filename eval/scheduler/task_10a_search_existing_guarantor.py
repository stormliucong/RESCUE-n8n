# task_10a_search_existing_guarantor.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode


class SearchExistingGuarantorTask(TaskInterface):
    def get_task_id(self) -> str:
        return "10a"

    def get_task_name(self) -> str:
        return "Search Existing Guarantor"

    def get_prompt(self) -> str:
        return """
Task: Search for patient's guarantor

Identify and confirm the guarantor responsible for this patient's insurance policy.
Patient's details:
- Name: John Doe
- ID: PAT001
"""

    def prepare_test_data(self) -> None:
        try:
            # Create patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "2010-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)

            # Create related person
            related_person_resource = {
                "resourceType": "RelatedPerson",
                "id": "REL001",
                "patient": {"reference": "Patient/PAT001"},
                "relationship": [{"text": "mother"}],
                "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
                "gender": "female",
                "birthDate": "1960-03-01"
            }
            self.upsert_to_fhir(related_person_resource)

            # Create account with guarantor
            account_resource = {
                "resourceType": "Account",
                "id": "ACC001",
                "status": "active",
                "subject": {"reference": "Patient/PAT001"},
                "guarantor": [{"party": {"reference": "RelatedPerson/REL001"}}]
            }
            self.upsert_to_fhir(account_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "patient": "Patient/PAT001"
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
        if 'entry' not in response_json or len(response_json['entry']) == 0:
            return ExecutionResult(
                execution_success=False,
                response_msg="No account found for patient PAT001"
            )

        account = response_json['entry'][0]['resource']
        if 'guarantor' not in account:
            return ExecutionResult(
                execution_success=False,
                response_msg="No guarantor found in account"
            )

        guarantor_reference = account['guarantor'][0]['party']['reference']
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found guarantor {guarantor_reference} for patient PAT001"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            params = {
                "patient": "Patient/PAT001"
            }

            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Account",
                headers=self.HEADERS,
                params=params
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one guarantor"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one account"
            
            account = response_json['entry'][0]['resource']
            assert 'guarantor' in account, "No guarantor found in account"
            guarantor_reference = account['guarantor'][0]['party']['reference']
            assert guarantor_reference == "RelatedPerson/REL001", "Invalid guarantor reference"

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