# task_12d_search_wednesday_morning_slots.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchWednesdayMorningSlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "12d"

    def get_task_name(self) -> str:
        return "Search Wednesday Morning Slots"

    def get_prompt(self) -> str:
        return """
Task: Search for Wednesday morning slots

Patient needs a visit on any Wednesday morning before 12pm one month from now. Find all available slots.

After searching, return all slot IDs using the following format: <SLOT_IDS>id1,id2,…</SLOT_IDS> and the total count using <SLOT_COUNT>number</SLOT_COUNT>
If none found, return the exact sentence: No Wednesday morning slots found
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
        all_slots = []
        for delta in range(1, 30):
            check_date = datetime.now() + timedelta(days=delta)
            if check_date.weekday() == 2:  # Wednesday
                start = check_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end = check_date.replace(hour=12, minute=0, second=0, microsecond=0)
                
                params = {
                    "start": [
                        f'ge{start.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                        f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'
                    ],
                    "status": "free"
                }
                
                response = requests.get(
                    f"{self.FHIR_SERVER_URL}/Slot",
                    headers=self.HEADERS,
                    params=params
                )
                
                if response.status_code == 200:
                    response_json = response.json()
                    if 'entry' in response_json:
                        all_slots.extend(response_json['entry'])
        
            if not all_slots:
                return ExecutionResult(
                    execution_success=False,
                    response_msg="No Wednesday morning slots found"
                )

            slot_ids = [entry['resource']['id'] for entry in all_slots]
            ids_str = ",".join(slot_ids)
            return ExecutionResult(
                execution_success=True,
                response_msg=(
                    f"Found {len(slot_ids)} available Wednesday morning slots: "
                    f"<SLOT_COUNT>{len(slot_ids)}</SLOT_COUNT> "
                    f"<SLOT_IDS>{ids_str}</SLOT_IDS>"
                )
            )
        

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:

            response_msg = execution_result.response_msg.strip()
            assert response_msg is not None, "Expected to find response message"
            human_agent_response = self.execute_human_agent()
            if "<SLOT_IDS>" not in human_agent_response.response_msg:
                assert "no wednesday morning slots found" in response_msg.lower(), "Expected to find no available slots"
            else:
                assert "<SLOT_IDS>" in response_msg, "Expected to find <SLOT_IDS> tag"
                assert "</SLOT_IDS>" in response_msg, "Expected to find </SLOT_IDS> tag"
                returned_ids = response_msg.split("<SLOT_IDS>")[1].split("</SLOT_IDS>")[0].split(",")
                expected_ids = human_agent_response.response_msg.split("<SLOT_IDS>")[1].split("</SLOT_IDS>")[0].split(",")
                assert returned_ids == expected_ids, f"Expected slot_ids {expected_ids}, got {returned_ids}"
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
