# task_14a_make_appointment_1.py
import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class MakeAppointmentTask(TaskInterface):
    def get_task_id(self) -> str:
        return "14a"

    def get_task_name(self) -> str:
        return "Make Appointment 1"

    def get_prompt(self) -> str:
        return """
Task: Make an appointment time for the patient John Doe with Provider Dr. John Smith on next Monday morning at 9am."

After creating the appointment and updating the slot, return the new Appointment ID using the following format: <APPOINTMENT>appointment_id</APPOINTMENT>
"""

    def prepare_test_data(self) -> None:
        try:
            practitioner1 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER001",
                "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
                "gender": "male",
                "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
                "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
            }
            self.upsert_to_fhir(practitioner1)
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
            patient1 = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient1)
            start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            start = start.replace(hour=9, minute=0, second=0, microsecond=0)
            slot1 = {
                "resourceType": "Slot",
                "id": "SLOT001",
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "free",
                "schedule": {"reference": "Schedule/SCHEDULE001"},
            }
            self.upsert_to_fhir(slot1)

            practitioner2 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER002",
                "name": [{"use": "official", "family": "John", "given": ["Smith"]}],
            }
            self.upsert_to_fhir(practitioner2)   
            start = datetime.now()
            end = start + timedelta(days=365)
            schedule2 = {
                "resourceType": "Schedule",
                "id": "SCHEDULE002",
                "actor": [{"reference": "Practitioner/PROVIDER002"}],
                "planningHorizon": {
                    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "specialty": [{"coding": [{"system": "http://snomed.info/sct", "code": "394580004", "display": "Clinical genetics"}]}],
            }
            self.upsert_to_fhir(schedule2)
            patient2 = {
                "resourceType": "Patient",
                "id": "PAT002",
                "name": [{"use": "official", "family": "Doe", "given": ["Jane"]}],
                "birthDate": "2020-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient2)
            start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            start = start.replace(hour=9, minute=0, second=0, microsecond=0)
            slot2 = {
                "resourceType": "Slot",
                "id": "SLOT002",
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "free",
                "schedule": {"reference": "Schedule/SCHEDULE002"},
            }
            self.upsert_to_fhir(slot2)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")



    def execute_human_agent(self) -> ExecutionResult:
        start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
        start = start.replace(hour=9, minute=0, second=0, microsecond=0)
        params = {
            "resourceType": "Appointment",
            "id": "APPOINTMENT001",
            "status": "booked",
            "slot": [{"reference": "Slot/SLOT001"}],
            "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
            "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/APPOINTMENT001", headers=self.HEADERS, json=params)
        # Added logic
        appointment_id = response.json().get('id')
        assert response.status_code in ['201','200'], f"Expected status code 201 or 200, but got {response.status_code}. Response body: {response.text}"
        params = {
            "resourceType": "Slot",
            "id": "SLOT001",
            "status": "busy",
        }
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/SLOT001", headers=self.HEADERS, json=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Successfully created appointment <APPOINTMENT>{appointment_id}</APPOINTMENT>"
        )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            start = start.replace(hour=9, minute=0, second=0, microsecond=0)
            # query appointment reference to slot1
            params = {
                "practitioner": "Practitioner/PROVIDER001",
                "date": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            # check the participant is correct
            assert 'entry' in response.json(), "Expected entry in the response"
            assert len(response.json()['entry']) == 1, "Expected one appointment" 
            assert response.json()['entry'][0]['resource']['participant'][0]['actor']['reference'] == "Patient/PAT001", "Expected patient reference to be PAT001"
            assert response.json()['entry'][0]['resource']['participant'][1]['actor']['reference'] == "Practitioner/PROVIDER001", "Expected practitioner reference to be PROVIDER001"
            # check the slot reference is busy
            slot_id = response.json()['entry'][0]['resource']['slot'][0]['reference']
            response = requests.get(f"{self.FHIR_SERVER_URL}/{slot_id}", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert response.json()['status'] == "busy", "Expected slot to be busy"

            
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
    
    
    
    