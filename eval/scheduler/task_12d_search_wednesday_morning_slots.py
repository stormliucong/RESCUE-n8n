# task_12d_search_wednesday_morning_slots.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class SearchWednesdayMorningSlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "12d"

    def get_task_name(self) -> str:
        return "Search Wednesday Morning Slots"

    def get_prompt(self) -> str:
        return """
Task: Search for Wednesday morning slots

Patient needs a visit on any Wednesday morning before 12pm one month from now. Find all available slots.
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
        
        return {"resourceType": "Bundle", "total": len(all_slots), "entry": all_slots}

    def validate_response(self, response: Any) -> TaskResult:
        try:
            start = datetime.now() + timedelta(days=35)
            assert 'total' in response, "Expected to find total in the response"
            assert response['total'] > 0, "Expected to find at least one slot"
            assert 'entry' in response, "Expected to find entry in the response"
            assert len(response['entry']) > 0, "Expected to find at least one slot"
            
            # Validate that all slots are on Wednesday mornings
            for entry in response['entry']:
                slot_time = datetime.strptime(entry['resource']['start'], "%Y-%m-%dT%H:%M:%SZ")
                assert slot_time.weekday() == 2, "All slots must be on Wednesday"
                assert 9 <= slot_time.hour < 12, "All slots must be in the morning before 12pm"
                date_delta = datetime.strptime(entry['resource']['start'], "%Y-%m-%dT%H:%M:%SZ") - start
                assert date_delta.days <= 0, "Expected to find followup slot within 30 days of one month from now"
                assert entry['resource']['status'] == "free", "Expected to find free slot"

            
            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "slots_found": response['total'],
                    "slots": [entry['resource'] for entry in response['entry']]
                }
            )

        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response
            )
        
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = SearchWednesdayMorningSlotsTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
    