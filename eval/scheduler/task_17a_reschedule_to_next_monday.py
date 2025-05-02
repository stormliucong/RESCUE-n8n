# task_17a_reschedule_to_next_monday.py
import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class RescheduleToNextMondayTask(TaskInterface):
    def get_task_id(self) -> str:
        return "17a"

    def get_task_name(self) -> str:
        return "Reschedule Today's Appointment to Next Monday at 9am"

    def get_prompt(self) -> str:
        return """
Task: Reschedule John Doe's (PAT001) appointment to next Monday with Dr. Smith.
"""

    def prepare_test_data(self) -> None:
        try:
            # Create patient
            patient1 = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient1)

            # Create practitioner
            practitioner1 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER001",
                "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
                "gender": "male",
                "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
                "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
            }
            self.upsert_to_fhir(practitioner1)
            
            # Create another practitioner
            practitioner2 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER002",
                "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
                "gender": "male",
            }
            self.upsert_to_fhir(practitioner2)

            # Create schedule
            start = datetime.now()
            end = start + timedelta(days=365)
            schedule1 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE001",
                "actor": [{"reference": "Practitioner/PROVIDER001"}],
                "planningHorizon": {
                    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
            }
            self.upsert_to_fhir(schedule1)
            
            # Create schedule for practitioner 2
            schedule2 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE002",
                "actor": [{"reference": "Practitioner/PROVIDER002"}],
            }
            self.upsert_to_fhir(schedule2)

            # Create slots for next 14 days, morning available only for practitioner 1
            j = 1
            for x in range(14):
                for i in range(9, 12):  # Morning hours only
                    if datetime.now().weekday() < 5:  # Weekdays only
                        start_time = datetime.now() + timedelta(days=x)
                        start_time = start_time.replace(hour=i, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)
                        
                        # First 2 days are busy, rest are free
                        status = "busy" if x < 2 else "free"
                        
                        slot = {
                            "resourceType": "Slot",
                            "id": f"SLOT00{j}",
                            "schedule": {"reference": "Schedule/SCHEDULE001"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": status,
                            "actor": [{"reference": "Practitioner/PROVIDER001"}]
                        }
                        self.upsert_to_fhir(slot)
                        j += 1
                        
            # Create slots for next 14 days, morning available only for practitioner 2
            for x in range(14):
                for i in range(9, 12):  # Morning hours only
                    if datetime.now().weekday() < 5:  # Weekdays only
                        start_time = datetime.now() + timedelta(days=x)
                        start_time = start_time.replace(hour=i, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)
                        
                        # First 7 days are busy, rest are free
                        status = "busy" if x < 7 else "free"    
                        
                        slot = {
                            "resourceType": "Slot",
                            "id": f"SLOT00{j}",
                            "schedule": {"reference": "Schedule/SCHEDULE002"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": status,
                            "actor": [{"reference": "Practitioner/PROVIDER002"}]
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

            # Create current appointment with practitioner 1 at today at 10am
            start_time = datetime.now()
            start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            # Find today's slot at 10am with practitioner 1
            params = {
                "schedule": "Schedule/SCHEDULE001",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the current slot"
            current_slot = response.json()['entry'][0]['resource']

            current_appointment = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT001",
                "status": "booked",
                "slot": [{"reference": f'Slot/{current_slot["id"]}'}],
                "participant": [
                    {"actor": {"reference": "Patient/PAT001"}, "status": "accepted"},
                    {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}
                ],
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(current_appointment)
            
            # Create another appointment with practitioner 2 at today at 11am
            start_time = datetime.now()
            start_time = start_time.replace(hour=11, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            # Find today's slot at 11am with practitioner 2
            params = {
                "schedule": "Schedule/SCHEDULE002",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the current slot"
            another_slot = response.json()['entry'][0]['resource']

            another_appointment = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT002",
                "status": "booked",
                "slot": [{"reference": f'Slot/{another_slot["id"]}'}],
                "participant": [
                    {"actor": {"reference": "Patient/PAT001"}, "status": "accepted"},
                    {"actor": {"reference": "Practitioner/PROVIDER002"}, "status": "accepted"}
                ],
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(another_appointment)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        # Find the current appointment
        params = {
            "patient": "Patient/PAT001",
            "practitioner": "Practitioner/PROVIDER001",
            "status": "booked",
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find the current appointment"
        assert len(response.json()['entry']) == 1, "Expected to find exactly one appointment"
        # bug in HAPI FHIR server, cancelled appointments are also returned
        # so we need to filter them out
        current_appointment = [entry['resource'] for entry in response.json()['entry'] if entry['resource']['status'] == 'booked']
        current_appointment = current_appointment[0]
        current_slot_reference = current_appointment['slot'][0]['reference']
        
        # Find next Monday's slot
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
        next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        params = {
            "schedule": "Schedule/SCHEDULE001",
            "status": "free",
            "start": next_monday.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find available slots"
        monday_slot = response.json()['entry'][0]['resource']
        
        # Update the current slot to free
        current_slot = requests.get(f"{self.FHIR_SERVER_URL}/{current_slot_reference}", headers=self.HEADERS).json()
        current_slot['status'] = 'free'
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{current_slot['id']}", headers=self.HEADERS, json=current_slot)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        # Update the Monday slot to busy
        monday_slot['status'] = 'busy'
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{monday_slot['id']}", headers=self.HEADERS, json=monday_slot)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        # Update the appointment to the new slot
        current_appointment['slot'] = [{"reference": f"Slot/{monday_slot['id']}"}]
        current_appointment['start'] = monday_slot['start']
        current_appointment['end'] = monday_slot['end']
        
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{current_appointment['id']}", headers=self.HEADERS, json=current_appointment)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Appointment rescheduled successfully to next Monday at 9am with slot: {monday_slot['id']}"
        )

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify that the current slot is free
            start_time = datetime.now()
            start_time = start_time.replace(hour=10, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            # Find today's slot at 10am with practitioner 1
            params = {
                "schedule": "Schedule/SCHEDULE001",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the current slot"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one slot"
            current_slot = response.json()['entry'][0]['resource']
            assert current_slot['status'] == 'free', "Expected current slot to be free"
            
            # Verify that next Monday's slot is busy
            next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
            
            params = {
                "schedule": "Schedule/SCHEDULE001",
                "start": next_monday.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find next Monday's slot"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one slot"
            monday_slot = response.json()['entry'][0]['resource']
            assert monday_slot['status'] == 'busy', "Expected Monday slot to be busy"
            
            # Verify that the appointment is updated correctly
            params = {
                "patient": "Patient/PAT001",
                "status": "booked",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the appointment"
            
            # HAPI FHIR server returns cancelled appointments, so we need to filter them out
            appointment = [entry['resource'] for entry in response.json()['entry'] if entry['resource']['status'] == 'booked']
            appointment = appointment[0]
            assert appointment['status'] == 'booked', "Expected appointment status to be 'booked'"
            assert appointment['participant'][0]['actor']['reference'] == 'Patient/PAT001', "Expected patient to be PAT001"
            assert appointment['participant'][1]['actor']['reference'] == 'Practitioner/PROVIDER001', "Expected practitioner to be PROVIDER001"
            
            # Verify the appointment is on Monday
            slot_id = appointment['slot'][0]['reference']
            response = requests.get(f"{self.FHIR_SERVER_URL}/{slot_id}", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            slot_start = datetime.strptime(response.json()['start'], "%Y-%m-%dT%H:%M:%SZ")
            assert slot_start.weekday() == 0, "Expected appointment to be on Monday"

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