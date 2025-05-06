# task_06b_search_nonexistent_surgery_plan.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonexistentSurgeryPlanTask(TaskInterface):
    def get_task_id(self) -> str:
        return "6b"

    def get_task_name(self) -> str:
        return "Search Nonexistent Surgery Plan"

    def get_prompt(self) -> str:
        return """
Task: Search for surgery plan

Search and find if patient id=PAT002 has any surgery plan two weeks from now.
"""

    def prepare_test_data(self) -> None:
        try:
            today = datetime.today().date()
            three_weeks_later = today + timedelta(days=21)

            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "1991-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)

            # Create service request for three weeks later (outside search window)
            service_request = {
                "resourceType": "ServiceRequest",
                "id": "APPENDECTOMY-REQUEST-002",
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
                    "reference": "Patient/PAT002"
                },
                "occurrenceDateTime": three_weeks_later.strftime("%Y-%m-%d")
            }
            self.upsert_to_fhir(service_request)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        today = datetime.today().date()
        two_weeks_later = today + timedelta(days=14)

        params = {
            "subject": "Patient/PAT002",
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
            response_msg=f"Found {response_json.get('total', 0)} surgery plan(s) for patient PAT001"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify no surgery plan was found
            today = datetime.today().date()
            two_weeks_later = today + timedelta(days=14)
            
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/ServiceRequest",
                headers=self.HEADERS,
                params={
                    "subject": "Patient/PAT001",
                    "occurrence": [
                        f"ge{today.isoformat()}",
                        f"le{two_weeks_later.isoformat()}"
                    ]
                }
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] == 0, f"Expected to find no surgery plans, but got {response_json['total']}"
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

    # def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
    #     # This method will be implemented with detailed failure mode analysis later
    #     return TaskFailureMode(
    #         incorrect_tool_selection=False,
    #         incorrect_tool_order=False,
    #         incorrect_resource_type=False,
    #         error_codes=None
    #     )
