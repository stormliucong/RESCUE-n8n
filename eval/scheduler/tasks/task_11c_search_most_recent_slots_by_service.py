# task_11c_search_most_recent_slots_by_service.py

import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class FindSlotsByServiceTask(TaskInterface):
    def get_task_id(self) -> str:
        return "11c"

    def get_task_name(self) -> str:
        return "Find Slots by Service"

    def get_prompt(self) -> str:
        return """
Task: Find available slots by service

Find the most recent available slots for a genetic counseling service.

After searching, return the total number of available slots using the following format: <SLOT_COUNT>number</SLOT_COUNT>
If none found, return the exact sentence: No available genetic counseling slots found
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
        # Find schedules with genetic counseling specialty
        schedule_params = {
            "specialty": "394580004"  # SNOMED CT code for Clinical genetics
        }
        schedules_response = requests.get(
            f"{self.FHIR_SERVER_URL}/Schedule",
            headers=self.HEADERS,
            params=schedule_params
        )
        
        if schedules_response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search schedules: {schedules_response.text}"
            )

        all_slots = []
        schedules_json = schedules_response.json()
        if 'entry' in schedules_json:
            for schedule in schedules_json['entry']:
                # Get free slots for this schedule
                slot_params = {
                    "schedule": f"Schedule/{schedule['resource']['id']}",
                    "status": "free",
                    "_sort": "start"
                }
                slots_response = requests.get(
                    f"{self.FHIR_SERVER_URL}/Slot",
                    headers=self.HEADERS,
                    params=slot_params
                )
                
                if slots_response.status_code != 200:
                    return ExecutionResult(
                        execution_success=False,
                        response_msg=f"Failed to search slots: {slots_response.text}"
                    )
                
                slots_json = slots_response.json()
                if 'entry' in slots_json:
                    all_slots.extend(slots_json['entry'])

        if not all_slots:
            return ExecutionResult(
                execution_success=True,
                response_msg="No available genetic counseling slots found"
            )

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {len(all_slots)} available genetic counseling slots: <SLOT_COUNT>{len(all_slots)}</SLOT_COUNT>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Structured-output assertions
                

            response_msg = execution_result.response_msg
            human_agent_response = self.execute_human_agent()
            if "<SLOT_COUNT>" not in human_agent_response.response_msg:
                assert "no available slots" in response_msg.lower(), f"Expected 'No available genetic counseling slots found', got '{response_msg}'"
            else:
                assert response_msg is not None, "Expected to find response message"
                response_msg = response_msg.strip()
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
            {"getAllResources": 0},
            {"getAllResources": 0, "getAllResources": 1},
            {"getAllResources": 0, "getResourceById": 1, "getAllResources": 2}
        ]

    def get_required_resource_types(self) -> list:
        return ["Slot"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 2