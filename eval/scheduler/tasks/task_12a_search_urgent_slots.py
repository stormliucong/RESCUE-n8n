# task_12a_search_urgent_slots.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchUrgentSlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "12a"

    def get_task_name(self) -> str:
        return "Search Urgent Slots"

    def get_prompt(self) -> str:
        return """
Task: Search for urgent slots

Patient needs an urgent visit by the end of tomorrow. Find all available slots.

After searching, return the number of available slots using the following format: <SLOT_COUNT>number</SLOT_COUNT>
If none found, return the exact sentence: No urgent slots available
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test practitioner
            practitioner = {
                "resourceType": "Practitioner",
                "id": "PROVIDER001",
                "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
                "gender": "male",
            }
            self.upsert_to_fhir(practitioner)

            # Create schedule
            schedule = {
                "resourceType": "Schedule",
                "id": "SCHEDULE001",
                "actor": [{"reference": "Practitioner/PROVIDER001"}],
                "planningHorizon": {
                    "start": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": (datetime.now() + timedelta(days=35)).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }
            self.upsert_to_fhir(schedule)

            # Create slots for next 35 days
            j = 1
            for x in range(35):
                for i in range(9, 12):  # Morning slots only
                    slot_start = datetime.now() + timedelta(days=x)
                    if slot_start.weekday() < 5:  # Weekdays only
                        slot_start = slot_start.replace(hour=i, minute=0, second=0, microsecond=0)
                        slot_end = slot_start + timedelta(hours=1)
                        
                        slot = {
                            "resourceType": "Slot",
                            "id": f"SLOT00{j}",
                            "schedule": {"reference": "Schedule/SCHEDULE001"},
                            "start": slot_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": slot_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": "free" if i % 2 == 0 else "busy"
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        start = datetime.now()
        end = start + timedelta(days=1)
        end = end.replace(hour=17, minute=0, second=0, microsecond=0)
        
        params = {
            "start": [
                f'gt{start.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'lt{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'
            ],
            "status": "free"
        }
        
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Slot",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search slots: {response.text}"
            )
            

        response_json = response.json()
        slots_found = response_json.get('total', 0)
        if slots_found > 0:
            return ExecutionResult(
                execution_success=True,
                response_msg=f"Found {slots_found} available slots for urgent visit: <SLOT_COUNT>{slots_found}</SLOT_COUNT>"
            )
        else:
            return ExecutionResult(
                execution_success=True,
                response_msg="No urgent slots available"
            )
        


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Structured-output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            human_agent_response = self.execute_human_agent()
            if "<SLOT_COUNT>" not in human_agent_response.response_msg:
                assert "no urgent slots available"  in response_msg.lower(), "Expected to find no available slots"
            else:
                assert "<SLOT_COUNT>" in response_msg, "Expected to find <SLOT_COUNT> tag"
                assert "</SLOT_COUNT>" in response_msg, "Expected to find </SLOT_COUNT> tag"
                slot_count = int(response_msg.split("<SLOT_COUNT>")[1].split("</SLOT_COUNT>")[0])
                expected_count = int(human_agent_response.response_msg.split("<SLOT_COUNT>")[1].split("</SLOT_COUNT>")[0])
                assert slot_count == expected_count, f"Expected slot_count {expected_count}, got {slot_count}"

        
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

    def get_required_tool_call_sets(self) -> list:
        return [
            {"getAllResources": 0}
        ]

    def get_required_resource_types(self) -> list:
        return ["Slot"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 2

    
    