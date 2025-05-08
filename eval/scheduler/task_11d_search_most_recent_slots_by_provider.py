# task_11d_search_most_recent_slots_by_provider.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class FindSlotsByProviderTask(TaskInterface):
    def get_task_id(self) -> str:
        return "11d"

    def get_task_name(self) -> str:
        return "Find Slots by Provider"

    def get_prompt(self) -> str:
        return """
Task: Find available slots by provider

Find the most recent available slots for Dr. Smith John

After searching, return the total number of available slots using the following format: <SLOT_COUNT>number</SLOT_COUNT>
If none found, return the exact sentence: No available slots found for Dr. Smith John
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
        # Find Dr. Smith John
        practitioner_params = {
            "family": "John",
            "given": "Smith"
        }
        practitioner_response = requests.get(
            f"{self.FHIR_SERVER_URL}/Practitioner",
            headers=self.HEADERS,
            params=practitioner_params
        )
        
        if practitioner_response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search practitioner: {practitioner_response.text}"
            )

        practitioner_json = practitioner_response.json()
        if 'entry' not in practitioner_json:
            return ExecutionResult(
                execution_success=False,
                response_msg="Practitioner not found"
            )

        practitioner_id = practitioner_json['entry'][0]['resource']['id']

        # Get schedules for this practitioner
        schedule_params = {
            "actor": f"Practitioner/{practitioner_id}"
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
                execution_success=False,
                response_msg="No available slots found for Dr. Smith John"
            )

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {len(all_slots)} available slots for Dr. Smith John: <SLOT_COUNT>{len(all_slots)}</SLOT_COUNT>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Find Dr. Smith John
            practitioner_params = {
                "family": "John",
                "given": "Smith"
            }
            practitioner_response = requests.get(
                f"{self.FHIR_SERVER_URL}/Practitioner",
                headers=self.HEADERS,
                params=practitioner_params
            )
            
            assert practitioner_response.status_code == 200, f"Expected status code 200, got {practitioner_response.status_code}"
            
            practitioner_json = practitioner_response.json()
            assert 'entry' in practitioner_json, "Expected to find practitioner"
            
            practitioner_id = practitioner_json['entry'][0]['resource']['id']
            assert practitioner_id == "PROVIDER001", f"Expected PROVIDER001, got {practitioner_id}"

            # Get schedules for this practitioner
            schedule_params = {
                "actor": f"Practitioner/{practitioner_id}"
            }
            schedules_response = requests.get(
                f"{self.FHIR_SERVER_URL}/Schedule",
                headers=self.HEADERS,
                params=schedule_params
            )
            
            assert schedules_response.status_code == 200, f"Expected status code 200, got {schedules_response.status_code}"
            
            all_slots = []
            schedules_json = schedules_response.json()
            assert 'entry' in schedules_json, "Expected to find entry in schedules response"
            
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
                
                assert slots_response.status_code == 200, f"Expected status code 200, got {slots_response.status_code}"
                slots_json = slots_response.json()
                if 'entry' in slots_json:
                    all_slots.extend(slots_json['entry'])

            assert len(all_slots) > 0, "Expected to find at least one slot"
            for slot in all_slots:
                assert slot['resource']['status'] == "free", "Expected to find free slot"
                assert slot['resource']['schedule']['reference'] == "Schedule/SCHEDULE001", "Expected slot to be from Dr. Smith's schedule"

            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            if all_slots:
                assert "<SLOT_COUNT>" in response_msg, "Expected to find <SLOT_COUNT> tag"
                assert "</SLOT_COUNT>" in response_msg, "Expected to find </SLOT_COUNT> tag"
                slot_count = int(response_msg.split("<SLOT_COUNT>")[1].split("</SLOT_COUNT>")[0])
                expected_count = len(all_slots)
                assert slot_count == expected_count, f"Expected slot_count {expected_count}, got {slot_count}"
            else:
                assert response_msg == "No available slots found for Dr. Smith John", f"Expected 'No available slots found for Dr. Smith John', got '{response_msg}'"

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