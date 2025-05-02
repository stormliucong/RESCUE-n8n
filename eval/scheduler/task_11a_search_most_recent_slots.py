# task_11a_search_most_recent_slots.py

import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

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
                "address": [{"use" : "work", "line": ["789 Pine St"], "city": "Los Angeles", "state": "CA"}],
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
                "address": [{"use" : "work", "line": ["321 Elm St"], "city": "Chicago", "state": "IL"}],
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

    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "status": "free",
            "_sort": "start"
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
        if not response_json.get('entry'):
            return ExecutionResult(
                execution_success=False,
                response_msg="No available slots found"
            )

        slot = response_json['entry'][0]
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found available slot {slot['resource']['id']} starting at {slot['resource']['start']}"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            params = {
                "status": "free",
                "_sort": "start"
            }
            
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Slot",
                headers=self.HEADERS,
                params=params
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            response_json = response.json()
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one slot"
            
            slot = response_json['entry'][0]
            assert slot['resource']['id'] == 'SLOT0010', f"Expected SLOT0010, got {slot['resource']['id']}"
            assert slot['resource']['status'] == "free", "Expected to find free slot"
            
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