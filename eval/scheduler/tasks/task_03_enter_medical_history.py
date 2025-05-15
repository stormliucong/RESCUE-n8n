# task_03_enter_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class EnterMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "3"

    def get_task_name(self) -> str:
        return "Enter Medical History"

    def get_prompt(self) -> str:
        return """
Task: Record a medical condition

Record a medical condition for the patient id=PAT001 in his medical history that he has a hypertension. 
Using SNOMED CT (http://snomed.info/sct) for coding.

Return the recorded condition's ID using the following format: <CONDITION>condition_id</CONDITION>
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")



    def execute_human_agent(self) -> ExecutionResult:
        condition_data = {
            "resourceType": "Condition",
            "subject": { "reference": "Patient/PAT001" },
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension"
                }],
                "text": "Hypertension"
            },
            "clinicalStatus": { "coding": [{ "code": "active" }] }
        }

        response = requests.post(
            f"{self.FHIR_SERVER_URL}/Condition",
            headers=self.HEADERS,
            json=condition_data
        )
        
        if response.status_code != 201:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to create medical condition: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Successfully created medical condition with ID: <CONDITION>{response_json.get('id')}</CONDITION>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the medical condition was created correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Condition",
                headers=self.HEADERS,
                params={"subject": "Patient/PAT001", "clinical-status": "active"}
            )
            
            assert response.status_code in [200, 201], f"Expected status code 200 or 201, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, f"Expected to find at least one condition, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, f"Expected to find at least one condition, but got {len(response_json['entry'])}"

            # Validate the condition details
            condition = response_json['entry'][0]['resource']
            assert condition['resourceType'] == "Condition", "Resource type must be Condition"
            assert condition['subject']['reference'] == "Patient/PAT001", "Subject reference must be Patient/PAT001"
            assert condition['clinicalStatus']['coding'][0]['code'] == "active", "Condition must be active"
            
            # Validate the condition code
            assert 'code' in condition, "Expected to find code in condition"
            assert condition['code']['coding'][0]['system'] == "http://snomed.info/sct", "Coding system must be SNOMED CT"
            assert condition['code']['coding'][0]['code'] == "38341003", "Invalid condition code"
            assert condition['code']['text'] == "Hypertension", "Invalid condition text"

            # Additional assertions (to be discussed)
            response_msg = execution_result.response_msg

            assert response_msg is not None, "Expected to find response message"

            response_msg = response_msg.strip()
                # match the response message with the expected format
            assert "<CONDITION>" in response_msg, "Expected to find <CONDITION> tag"
            assert "</CONDITION>" in response_msg, "Expected to find </CONDITION>tag"
            
                # Extract the condition_id from the response message
            condition_id = response_msg.split("<CONDITION>")[1].split("</CONDITION>")[0]

            assert condition_id is not None, "Expected to find condition_id"

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
