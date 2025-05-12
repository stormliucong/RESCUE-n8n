# task_12b_search_next_friday_slots.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchNextFridaySlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "12b"

    def get_task_name(self) -> str:
        return "Search Next Friday Slots"

    def get_prompt(self) -> str:
        return """
Task: Search for next Friday slots

Patient needs a general visit on next Friday. Find all available slots.

After searching, return all slot IDs using the following format: <SLOT_IDS>id1,id2,…</SLOT_IDS>
If none found, return the exact sentence: No available slots for next Friday

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
        start = datetime.now() + timedelta(days=7)
        next_friday = start + timedelta(days=(4 - start.weekday()) % 7)
        next_friday = next_friday.replace(hour=9, minute=0, second=0, microsecond=0)
        end = next_friday.replace(hour=17, minute=0, second=0, microsecond=0)
        
        params = {
            "start": [
                f'ge{next_friday.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'
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

        slots = response_json.get('entry', [])
        if not slots:
            return ExecutionResult(
                execution_success=True,
                response_msg="No available slots for next Friday"
            )

        slot_ids = [e['resource']['id'] for e in slots]
        ids_str = ",".join(slot_ids)
        return ExecutionResult(
            execution_success=True,
            response_msg=(
                f"Found {len(slot_ids)} available slots for next Friday: "
                f"<SLOT_IDS>{ids_str}</SLOT_IDS>"
            )
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            start = datetime.now() + timedelta(days=7)
            next_friday = start + timedelta(days=(4 - start.weekday()) % 7)
            next_friday = next_friday.replace(hour=9, minute=0, second=0, microsecond=0)
            end = next_friday.replace(hour=17, minute=0, second=0, microsecond=0)
            
            params = {
                "start": [
                    f'ge{next_friday.strftime("%Y-%m-%dT%H:%M:%SZ")}',
                    f'le{end.strftime("%Y-%m-%dT%H:%M:%SZ")}'
                ],
                "status": "free"
            }
            
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Slot",
                headers=self.HEADERS,
                params=params
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one slot"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) == 1, "Expected to find exactly one slot"
            for entry in response_json['entry']:
                assert entry['resource']['start'].startswith(next_friday.strftime("%Y-%m-%d")), "Expected to find next friday slot"
                assert entry['resource']['status'] == "free", "Expected to find free slot"
                
            # Additional eval logic
            response_msg = execution_result.response_msg.strip()
            if response_json.get('total', 0) > 0:
                assert "<SLOT_IDS>" in response_msg, "Expected to find <SLOT_IDS> tag"
                assert "</SLOT_IDS>" in response_msg, "Expected to find </SLOT_IDS> tag"
                returned_ids = response_msg.split("<SLOT_IDS>")[1].split("</SLOT_IDS>")[0].split(",")
                expected_ids = [e['resource']['id'] for e in response_json['entry']]
                assert returned_ids == expected_ids, f"Expected slot_ids {expected_ids}, got {returned_ids}"
            else:
                assert response_msg == "No available slots for next Friday", f"Expected 'No available slots for next Friday', got '{response_msg}'"

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
