# task_06a_search_existing_surgery_plan.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchExistingSurgeryPlanTask(TaskInterface):
    def get_task_id(self) -> str:
        return "6a"

    def get_task_name(self) -> str:
        return "Search Existing Surgery Plan"

    def get_prompt(self) -> str:
        return """
Task: Search for surgery plan

Search and find if patient id=PAT001 has any surgery plan two weeks from now.

If found, return the surgery plan’s ID using the following format: <SURGERY_PLAN>plan_id</SURGERY_PLAN>
"""

    def prepare_test_data(self) -> None:
        try:
            today = datetime.today().date()
            one_week_later = today + timedelta(days=7)

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

            # Create service request for next week
            service_request = {
                "resourceType": "ServiceRequest",
                "id": "APPENDECTOMY-REQUEST-001",
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
                "occurrenceDateTime": one_week_later.strftime("%Y-%m-%d")
            }
            self.upsert_to_fhir(service_request)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")


    def execute_human_agent(self) -> ExecutionResult:
        today = datetime.today().date()
        two_weeks_later = today + timedelta(days=14)

        params = {
            "subject": "Patient/PAT001",
            "occurrence": [
                f"ge{today.isoformat()}",
                f"le{two_weeks_later.isoformat()}"
            ]
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/ServiceRequest",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for surgery plans: {response.text}"
            )

        response_json = response.json()
        return ExecutionResult(
            execution_success=True,
            response_msg=(
                f"Found {response_json.get('total', 0)} surgery plan(s) for patient PAT001: "
                f"<SURGERY_PLAN>{response_json['entry'][0]['resource']['id']}</SURGERY_PLAN>"
            )
        )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            
             # Structured‐output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<SURGERY_PLAN>" in response_msg, "Expected to find <SURGERY_PLAN> tag"
            assert "</SURGERY_PLAN>" in response_msg, "Expected to find </SURGERY_PLAN> tag"
            surgery_plan_id = response_msg.split("<SURGERY_PLAN>")[1].split("</SURGERY_PLAN>")[0]
            assert surgery_plan_id is not None, "Expected to find surgery_plan_id"
            expected_id = self.execute_human_agent().response_msg.split("<SURGERY_PLAN>")[1].split("</SURGERY_PLAN>")[0]
            assert surgery_plan_id == expected_id, f"Expected surgery_plan_id {expected_id}, got {surgery_plan_id}"

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
        return ["ServiceRequest"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 1



