# task_11b_search_most_recent_slots_by_language.py

import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode
import logging

logger = logging.getLogger(__name__)

class FindAvailableSlotsTask(TaskInterface):
    def get_task_id(self) -> str:
        return "11b"

    def get_task_name(self) -> str:
        return "Find Available Slots by Language"

    def get_prompt(self) -> str:
        return """
Task: Find available slots

Find most recent available slots from any providers who can speak spanish, was a female and working at Boston. 
Return the Slot ID from the FHIR server. 
Using the following format:
```
<response>
    <slot_id>SLOT0010</slot_id>
</response>
```
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
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "zh"}]},
                    {"coding": [{"system": "urn:ietf:bcp:47", "code": "es"}]}

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
            # create 4 schedules with 3 slots each
            # each schedule should have 3 slots with 1 hour apart
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
        
        # Search for practitioners who can speak spanish, was a female and working at Boston
        params = {
            "gender": "female",
            "address-city": "Boston",
            "communication": "es"
        }
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Practitioner",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search practitioners: {response.text}"
            )
        else:
            response_json = response.json()
            if not response_json.get('entry'):
                return ExecutionResult(
                    execution_success=False,
                    response_msg="No practitioners found"
                )
            else:
                practitioner_ids = [entry['resource']['id'] for entry in response_json['entry']]
                logger.debug(f"Found {len(practitioner_ids)} practitioners: {practitioner_ids}")
                
                # Search fo most slot among all available slots for each practitioner    
                most_recent_slot = None
                for practitioner_id in practitioner_ids:
                    # get the schedule
                    params = {
                        "status": "free",
                        "_sort": "start",
                        "schedule.actor": f"Practitioner/{practitioner_id}"
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
                    else:
                        response_json = response.json()
                        if not response_json.get('entry'):
                            logger.debug(f"No slots found for practitioner {practitioner_id}")
                        else:
                            
                            for slot in response_json['entry']:
                                logger.debug(f"Slot {slot['resource']['id']} starting at {slot['resource']['start']}")
                                # find the slot with the most recent start time
                                if most_recent_slot is None or slot['resource']['start'] < most_recent_slot['resource']['start']:
                                    most_recent_slot = slot

                            logger.debug(f"Found available slot {most_recent_slot['resource']['id']} starting at {most_recent_slot['resource']['start']}")
                            tagged_response = f'''<response>
                                                    <slot_id>{most_recent_slot['resource']['id']}</slot_id>
                                                </response>
                                                '''
                            return ExecutionResult(
                                execution_success=True,
                                response_msg=f"Found available slot {tagged_response} starting at {most_recent_slot['resource']['start']}"
                            )
       
    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            params = {
                "status": "free",
                "_sort": "start"
            }
            
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            
            # Parse the response message
            response_msg = response_msg.strip()
            # match the response message with the expected format
            assert "<response>" in response_msg, "Expected to find <response> tag"
            assert "</response>" in response_msg, "Expected to find </response> tag"
            assert "<slot_id>" in response_msg, "Expected to find <slot_id> tag"
            assert "</slot_id>" in response_msg, "Expected to find </slot_id> tag"
            
            # Extract the slot_id from the response message
            slot_id = response_msg.split("<slot_id>")[1].split("</slot_id>")[0]
            assert slot_id is not None, "Expected to find slot_id"
            
            # slot id should be 
            expected_slot_id = self.execute_human_agent().response_msg.split("<slot_id>")[1].split("</slot_id>")[0]
            assert slot_id == expected_slot_id, f"Expected slot_id {expected_slot_id}, got {slot_id}"
            
             
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
    # load the environment variables
    import os
    from dotenv import load_dotenv
    load_dotenv()
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")
    HEADERS = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    
    task = FindAvailableSlotsTask(fhir_server_url=FHIR_SERVER_URL, n8n_url=N8N_URL, n8n_execution_url=N8N_EXECUTION_URL)
    task.delete_all_resources()
    task.prepare_test_data()
    execution_result = task.execute_human_agent()
    task_result = task.validate_response(execution_result)
    print(task_result)