# eval/scheduler/task_04a_search_existing_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNonemptyMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "4a"

    def get_task_name(self) -> str:
        return "Search Existing Medical History"

    def get_prompt(self) -> str:
        return """
Task: Search for patient medical history

Search for the existing patient id=PAT001 to see if he has any medical history.

If found, return the condition's ID using the following format: <CONDITION>condition_id</CONDITION>
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
            # Create condition for the patient
            condition_data = {
                "resourceType": "Condition",
                "id": "Appendicitis001",
                "subject": { "reference": "Patient/PAT001" },
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "74400008",
                        "display": "Appendicitis"
                    }],
                    "text": "Appendicitis"
                },
                "clinicalStatus": { "coding": [{ "code": "active" }] }
            }
            self.upsert_to_fhir(condition_data)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")


    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "subject": "Patient/PAT001"
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
            response_msg=f"Found {response_json.get('total', 0)} medical condition(s) for patient PAT001: <CONDITION>{response.json()['entry'][0]['resource']['id']}</CONDITION>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Check if returned result matches the human executed request's return.
            response_msg = execution_result.response_msg

            assert response_msg is not None, "Expected to find response message"

            response_msg = response_msg.strip()
                # match the response message with the expected format
            assert "<CONDITION>" in response_msg, "Expected to find <CONDITION> tag"
            assert "</CONDITION>" in response_msg, "Expected to find </CONDITION>tag"
            
                # Extract the condition_id from the response message
            condition_id = response_msg.split("<CONDITION>")[1].split("</CONDITION>")[0]

            assert condition_id is not None, "Expected to find condition_id"

            expected_condition_id = self.execute_human_agent().response_msg.split("<CONDITION>")[1].split("</CONDITION>")[0]
            assert condition_id == expected_condition_id, f"Expected condition_id {expected_condition_id}, got {condition_id}"
            
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

# if __name__ == "__main__":
#     from dotenv import load_dotenv
#     load_dotenv()
    
#     FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
#     N8N_URL = os.getenv("N8N_AGENT_URL")
#     N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")

    
#     task = SearchNonemptyMedicalHistoryTask(FHIR_SERVER_URL, N8N_URL, N8N_EXECUTION_URL)
#     print(task.get_task_id())
#     print(task.get_task_name())
#     task.cleanup_test_data()
#     task.prepare_test_data()
#     human_response = task.execute_human_agent()
#     # eval_results = task.validate_response(human_response)
#     print(human_response)
#     # n8n_response = task.execute_n8n_agent()
#     # print(n8n_response)