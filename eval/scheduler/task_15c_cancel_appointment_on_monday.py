import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class CancelAppointmentOnMondayTask(TaskInterface):
    def get_task_id(self) -> str:
        return "15c"

    def get_task_name(self) -> str:
        return "Cancel Appointment on Monday"

    def get_prompt(self) -> str:
        return """
Task: Cancel Patient John Doe's appointment on next Monday.

After cancelling, return the cancelled appointment ID and freed slot ID using:
<APPOINTMENT>appointment_id</APPOINTMENT>
<SLOT_ID>slot_id</SLOT_ID>
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

            # Create Monday appointment
            next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
            slot1 = {
                "resourceType": "Slot",
                "id": "SLOT001",
                "start": next_monday.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (next_monday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "busy",
                "schedule": {"reference": "Schedule/SCHEDULE001"},
            }
            self.upsert_to_fhir(slot1)
            appointment1 = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT001",
                "status": "booked",
                "slot": [{"reference": "Slot/SLOT001"}],
                "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, 
                              {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
                "start": next_monday.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (next_monday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(appointment1)

            # Create Tuesday appointment
            next_tuesday = next_monday + timedelta(days=1)
            slot2 = {
                "resourceType": "Slot",
                "id": "SLOT002",
                "start": next_tuesday.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (next_tuesday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "busy",
                "schedule": {"reference": "Schedule/SCHEDULE001"},
            }
            self.upsert_to_fhir(slot2)
            appointment2 = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT002",
                "status": "booked",
                "slot": [{"reference": "Slot/SLOT002"}],
                "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, 
                              {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
                "start": next_tuesday.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (next_tuesday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(appointment2)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        # Find the appointment on next Monday
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
        next_monday_date = next_monday.date()
        
        params = {
            "patient": "Patient/PAT001",
            "status": "booked",
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find at least one appointment"
        
        # Find the appointment on next Monday
        appointment_to_cancel = None
        for appointment in response.json()['entry']:
            # Double check the appointment status is actually booked
            if appointment['resource']['status'] != 'booked':
                continue
                
            slot = appointment['resource']['slot'][0]['reference']
            slot_response = requests.get(f"{self.FHIR_SERVER_URL}/{slot}", headers=self.HEADERS)
            assert slot_response.status_code == 200, f"Expected status code 200, but got {slot_response.status_code}. Response body: {slot_response.text}"
            start_date = datetime.strptime(slot_response.json()['start'], "%Y-%m-%dT%H:%M:%SZ").date()
            if start_date == next_monday_date:
                appointment_to_cancel = appointment
                break

        assert appointment_to_cancel is not None, "Expected to find an appointment on next Monday"
        
        # Cancel the appointment by updating its status to 'cancelled'
        appointment_id = appointment_to_cancel['resource']['id']
        slot_id = appointment_to_cancel['resource']['slot'][0]['reference'].split('/')[-1]
        
        # Update appointment status to cancelled
        params = {
            "resourceType": "Appointment",
            "id": appointment_id,
            "status": "cancelled",
            "slot": appointment_to_cancel['resource']['slot'],
            "participant": appointment_to_cancel['resource']['participant'],
            "start": appointment_to_cancel['resource']['start'],
            "end": appointment_to_cancel['resource']['end'],
        }
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{appointment_id}", headers=self.HEADERS, json=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        # Update slot status back to free
        params = {
            "resourceType": "Slot",
            "id": slot_id,
            "status": "free",
            "start": next_monday.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": (next_monday + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schedule": {"reference": "Schedule/SCHEDULE001"},
        }
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{slot_id}", headers=self.HEADERS, json=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        return ExecutionResult(
            execution_success=True,
            response_msg=(
                f"Successfully cancelled appointment <APPOINTMENT>{appointment_id}</APPOINTMENT> "
                f"and freed slot <SLOT_ID>{slot_id}</SLOT_ID>"
            )
        )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify that the Monday appointment is cancelled
            next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            next_monday_date = next_monday.date()
            
            # First check the cancelled appointment
            params = {
                "patient": "Patient/PAT001",
                "status": "cancelled",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the cancelled appointment"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one cancelled appointment"
            
            # Verify that the cancelled appointment is on Monday
            slot_id = response.json()['entry'][0]['resource']['slot'][0]['reference']
            response = requests.get(f"{self.FHIR_SERVER_URL}/{slot_id}", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            start_date = datetime.strptime(response.json()['start'], "%Y-%m-%dT%H:%M:%SZ").date()
            assert start_date == next_monday_date, "Expected cancelled appointment to be on next Monday"
            assert response.json()['status'] == "free", "Expected slot to be free after cancellation"

            # Verify that the Tuesday appointment is still booked
            params = {
                "patient": "Patient/PAT001",
                "status": "booked",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the other appointment still booked"
            # 
            # Filter out any cancelled appointments from the response
            booked_appointments = [appt for appt in response.json()['entry'] 
                                if appt['resource']['status'] == 'booked']
            assert len(booked_appointments) == 1, "Expected to find exactly one booked appointment"

            # Additional eval
            response_msg = execution_result.response_msg.strip()
            assert "<APPOINTMENT>" in response_msg and "</APPOINTMENT>" in response_msg, "Missing <APPOINTMENT> tag"
            assert "<SLOT_ID>" in response_msg and "</SLOT_ID>" in response_msg, "Missing <SLOT_ID> tag"

            appointment_id = response_msg.split("<APPOINTMENT>")[1].split("</APPOINTMENT>")[0]
            slot_id = response_msg.split("<SLOT_ID>")[1].split("</SLOT_ID>")[0]

            # Verify appointment is cancelled
            appt_resp = requests.get(f"{self.FHIR_SERVER_URL}/Appointment/{appointment_id}", headers=self.HEADERS)
            assert appt_resp.status_code == 200 and appt_resp.json().get("status") == "cancelled", f"Appointment {appointment_id} not cancelled"

            # Verify slot is free
            slot_resp = requests.get(f"{self.FHIR_SERVER_URL}/Slot/{slot_id}", headers=self.HEADERS)
            assert slot_resp.status_code == 200 and slot_resp.json().get("status") == "free", f"Slot {slot_id} not freed"

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
