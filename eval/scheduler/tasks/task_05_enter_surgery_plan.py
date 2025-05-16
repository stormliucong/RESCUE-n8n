# eval/scheduler/task_05_enter_surgery_plan.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class EnterSurgeryPlanTask(TaskInterface):
    def get_task_id(self) -> str:
        return "5"

    def get_task_name(self) -> str:
        return "Enter Surgery Plan"

    def get_prompt(self) -> str:
        return """
Task: Record a surgery plan

Record a surgery plan for patient id=PAT001 for a Appendectomy surgery planned for 2025-05-01.

Once done, return the surgery plan ID in the following format: <surgery_plan>surgeryPlan</surgery_plan>

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
        service_request = {
            "resourceType": "ServiceRequest",
            "status": "active",
            "intent": "order",
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "80146002",
                    "display": "Appendectomy (procedure)"
                }],
                "text": "Appendectomy"
            },
            "subject": {
                "reference": "Patient/PAT001"
            },
            "occurrenceDateTime": "2025-05-01"
        }

        response = requests.post(
            f"{self.FHIR_SERVER_URL}/ServiceRequest",
            headers=self.HEADERS,
            json=service_request
        )
        
        if response.status_code != 201:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to create surgery plan: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Successfully created surgery plan with ID <surgery_plan>{response_json.get('id')}</surgery_plan>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the surgery plan was created correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/ServiceRequest",
                headers=self.HEADERS,
                params={"subject": "Patient/PAT001", "status": "active"}
            )
            
            assert response.status_code in [200, 201], f"Expected status code 200 or 201, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, f"Expected to find at least one surgery plan, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, f"Expected to find at least one surgery plan, but got {len(response_json['entry'])}"

            # Validate the service request details
            service_request = response_json['entry'][0]['resource']
            assert service_request['resourceType'] == "ServiceRequest", "Resource type must be ServiceRequest"
            assert service_request['status'] == "active", "Service request must be active"
            assert service_request['intent'] == "order", "Service request intent must be order"
            assert service_request['subject']['reference'] == "Patient/PAT001", "Subject reference must be Patient/PAT001"
            
            # Validate the procedure code
            assert 'code' in service_request, "Expected to find code in service request"
            assert service_request['code']['coding'][0]['code'] == "80146002", "Invalid procedure code"
            assert service_request['code']['text'] == "Appendectomy", "Invalid procedure text"
            
            # Validate the scheduled date
            assert service_request['occurrenceDateTime'] == "2025-05-01", "Incorrect surgery date"


            # Check if returned result matches the human executed request's return.
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"

            # Parse the response message
            response_msg = response_msg.strip()
            # match the response message with the expected format
            assert "<surgery_plan>" in response_msg, "Expected to find <surgery_plan> tag"
            assert "</surgery_plan>" in response_msg, "Expected to find </surgery_plan>tag"

            # Extract the surgery_plan from the response message
            surgery_plan = response_msg.split("<surgery_plan>")[1].split("</surgery_plan>")[0]
            assert surgery_plan is not None, "Expected to find surgery_plan"

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
            {"getAllResources": 0, "createResource": 1}
        ]

    def get_required_resource_types(self) -> list:
        return ["ServiceRequest"]

    def get_prohibited_tools(self) -> list:
        return ["deleteResource"]

    def get_difficulty_level(self) -> int:
        return 2
