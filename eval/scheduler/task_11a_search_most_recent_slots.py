# task_11a_search_most_recent_slots.py

import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class FindAvailableSlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "11a"

    def get_task_name(self) -> str:
        return "Find Available Slots"

    def get_prompt(self) -> str:
        return """
Task: Find available slots

Find most recent available slots from any providers.
"""

    def prepare_test_data(self) -> None:
        try:
            practitioner = {
                "resourceType": "Practitioner",
                "id": "PROVIDER001",
                "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
                "gender": "male",
                "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
                "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
            }

            # Add more practitioners with diverse attributes
            practitioner2 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER002",
                "name": [{"use": "official", "family": "Chen", "given": ["Wei"]}],
                "gender": "female",
                "communication": [
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "zh"}]}
                ],
                "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
            }

            practitioner3 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER003",
                "name": [{"use": "official", "family": "Garcia", "given": ["Maria", "Isabel"]}],
                "gender": "female",
                "communication": [
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "es"}]}
                ],
                "address": [{"use": "work", "line": ["789 Pine St"], "city": "Los Angeles", "state": "CA"}],
            }

            practitioner4 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER004",
                "name": [{"use": "official", "family": "Patel", "given": ["Rajesh"]}],
                "gender": "male",
                "communication": [
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]},
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "hi"}]}
                ],
                "address": [{"use": "work", "line": ["321 Elm St"], "city": "Chicago", "state": "IL"}],
            }

            # Upsert all practitioners to FHIR server
            self.upsert_to_fhir(practitioner)
            self.upsert_to_fhir(practitioner2)
            self.upsert_to_fhir(practitioner3)
            self.upsert_to_fhir(practitioner4)

            schedule = {
                "resourceType": "Schedule",
                "id": "SCHEDULE001",
                "actor": [{"reference": "Practitioner/PROVIDER001"}],
                "planningHorizon": {
                    "start": "2025-04-11T00:00:00Z",
                    "end": "2026-04-11T00:00:00Z"
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
            }

            self.upsert_to_fhir(schedule)
            schedule2 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE002",
                "actor": [{"reference": "Practitioner/PROVIDER002"}],
                "planningHorizon": {
                    "start": "2025-04-11T00:00:00Z",
                    "end": "2026-04-11T00:00:00Z"
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "408459003", "display": "Pediatric cardiology"}]}],
            }
            self.upsert_to_fhir(schedule2)

            schedule3 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE003",
                "actor": [{"reference": "Practitioner/PROVIDER003"}],
                "planningHorizon": {
                    "start": "2025-04-11T00:00:00Z",
                    "end": "2026-04-11T00:00:00Z"
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
            }
            self.upsert_to_fhir(schedule3)

            schedule4 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE004",
                "actor": [{"reference": "Practitioner/PROVIDER004"}],
                "planningHorizon": {
                    "start": "2025-04-11T00:00:00Z",
                    "end": "2026-04-11T00:00:00Z"
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
            }
            self.upsert_to_fhir(schedule4)

            j = 1
            for k in range(4):
                for i in range(9, 12):
                    schedule_id = f"SCHEDULE00{k+1}"
                    start = datetime.now() + timedelta(days=1)
                    start = start.replace(hour=i, minute=0, second=0, microsecond=0)
                    # convert it to 2025-04-11T00:00:00Z
                    # end is tomorrow at 9am
                    end = start + timedelta(hours=1)
                    # convert it to 2025-04-11T00:00:00Z
                    start = start.strftime("%Y-%m-%dT%H:%M:%SZ")
                    end = end.strftime("%Y-%m-%dT%H:%M:%SZ")
                    # status is free for even i, busy for odd i
                    status = "free" if (i+k) % 4 == 0 else "busy" 
                    # first one should be k = 3, i = 9, j = 10
                    slot = {
                        "resourceType": "Slot",
                        "id": f"SLOT00{j}",
                        "schedule": {"reference": f"Schedule/{schedule_id}"},
                        "start": start,
                        "end": end,
                        "status": status
                    }    
                    self.upsert_to_fhir(slot)
                    j += 1
                    
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        params = {
            "status": "free",
            "_sort": "start"
        }
        
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Slot",
            headers=self.HEADERS,
            params=params
        )
        
        return response.json()['entry'][0]

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response['resource']['id'] == 'SLOT0010', f"Expected SLOT0010, got {response['resource']['id']}"
                  
            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "slots": response
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
    
    task = FindAvailableSlotsTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)