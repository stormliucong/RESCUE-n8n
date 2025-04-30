# task_12b_search_next_friday_slots.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class SearchNextFridaySlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "12b"

    def get_task_name(self) -> str:
        return "Search Next Friday Slots"

    def get_prompt(self) -> str:
        return """
Task: Search for next Friday slots

Patient needs a general visit on next Friday. Find all available slots.
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


    def execute_human_agent(self) -> Dict:
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
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
        
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            next_friday = datetime.now() + timedelta(days=7)
            next_friday = next_friday + timedelta(days=(4 - next_friday.weekday()) % 7)
            print(f"Next friday: {next_friday}")
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one slot"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) == 1, "Expected to find exactly one slot"
            for entry in response_json['entry']:
                assert entry['resource']['start'].startswith(next_friday.strftime("%Y-%m-%d")), "Expected to find next friday slot"
                assert entry['resource']['status'] == "free", "Expected to find free slot"
            
            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "slots_found": response_json['total'],
                    "slots": [entry['resource'] for entry in response_json['entry']]
                }
            )

        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response.json() if hasattr(response, 'json') else response
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_data=response.json() if hasattr(response, 'json') else response
            )
        
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = SearchNextFridaySlotsTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
    