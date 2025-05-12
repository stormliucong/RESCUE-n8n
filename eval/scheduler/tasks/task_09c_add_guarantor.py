# task_09c_add_guarantor.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class AddGuarantorTask(TaskInterface):
    def get_task_id(self) -> str:
        return "9c"

    def get_task_name(self) -> str:
        return "Add Guarantor"

    def get_prompt(self) -> str:
        return """
Task: Add a guarantor to an account

Add the related person REL001 as a guarantor to the account ACC001 with the following details:
- Relationship: Mother

After updating, return the account ID using the following format: <ACCOUNT>account_id</ACCOUNT>

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

            # Create related person (mother)
            related_person_resource = {
                "resourceType": "RelatedPerson",
                "id": "REL001",
                "patient": {"reference": "Patient/PAT001"},
                "relationship": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "MOTHER"
                    }],
                    "text": "mother"
                }],
                "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
                "gender": "female",
                "birthDate": "1960-03-01"
            }
            self.upsert_to_fhir(related_person_resource)

            # Create initial account
            account_payload = {
                "resourceType": "Account",
                "id": "ACC001",
                "status": "active",
                "subject": {"reference": "Patient/PAT001"}
            }
            response = requests.post(
                f"{self.FHIR_SERVER_URL}/Account",
                headers=self.HEADERS,
                json=account_payload
            )
            if response.status_code != 201:
                raise Exception("Failed to create initial account")

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")


    def execute_human_agent(self) -> Dict:
        update_payload = {
            "resourceType": "Account",
            "id": "ACC001",
            "status": "active",
            "subject": {"reference": "Patient/PAT001"},
            "guarantor": [{
                "party": {"reference": "RelatedPerson/REL001"}
            }]
        }
        
        # Update the account
        response = requests.put(
            f"{self.FHIR_SERVER_URL}/Account/ACC001",
            headers=self.HEADERS,
            json=update_payload
        )
        
        if response.status_code not in [200, 201]:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to update account: {response.text}"
            )

        response_json = response.json()
        account_id = response_json.get('id')
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Updated account with ID <ACCOUNT>{account_id}</ACCOUNT>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the account was updated correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Account/ACC001",
                headers=self.HEADERS
            )
            
            response_json = response.json()
            assert response_json["resourceType"] == "Account", "Invalid resource type"
            assert response_json["status"] == "active", "Account status should be active"
            assert "guarantor" in response_json, "Guarantor not added to account"
            assert response_json["guarantor"][0]["party"]["reference"] == "RelatedPerson/REL001", "Invalid guarantor reference"

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