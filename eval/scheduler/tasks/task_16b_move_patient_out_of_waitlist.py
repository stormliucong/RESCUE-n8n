import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class MovePatientOutOfWaitlistTask(TaskInterface):
    def get_task_id(self) -> str:
        return "16b"

    def get_task_name(self) -> str:
        return "Move Patient Out of Waitlist"

    def get_prompt(self) -> str:
        return """
Task: Move patient John Doe (PAT001) out of the waitlist by booking them into an available slot with Dr. Smith.

After moving, return the appointment ID and slot ID using the following format:
<APPOINTMENT>appointment_id</APPOINTMENT>
<SLOT_ID>slot_id</SLOT_ID>
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

            # Create slots for next 14 days, morning available only
            j = 1
            for x in range(1,14):
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
                            "schedule": {"reference": "Schedule/SCHEDULE001"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": status
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

            # Create a waitlist appointment
            start = datetime.now() + timedelta(days=1)
            start = start.replace(hour=9, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=6)
            waitlist_appointment = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT001",
                "status": "waitlist",
                "participant": [
                    {"actor": {"reference": "Patient/PAT001"}, "status": "accepted"},
                    {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}
                ],
                "requestedPeriod": {
                    "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": end.strftime("%Y-%m-%dT%H:%M:%SZ")
                }
            }
            self.upsert_to_fhir(waitlist_appointment)
            
            # make the SLOT002 10am slots free
            slot002 = requests.get(f"{self.FHIR_SERVER_URL}/Slot/SLOT002", headers=self.HEADERS)
            slot002 = slot002.json()
            slot002['status'] = 'free'
            response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/SLOT002", headers=self.HEADERS, json=slot002)            
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")



    def execute_human_agent(self) -> ExecutionResult:
        # Find the waitlist appointment
        params = {
            "patient": "Patient/PAT001",
            "status": "waitlist",
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find the waitlist appointment"
        assert len(response.json()['entry']) == 1, "Expected to find exactly one waitlist appointment"
        
        waitlist_appointment = response.json()['entry'][0]['resource']
        
        # Find an available slot within the requested period
        start_date = datetime.strptime(waitlist_appointment['requestedPeriod'][0]['start'], "%Y-%m-%dT%H:%M:%SZ")
        end_date = datetime.strptime(waitlist_appointment['requestedPeriod'][0]['end'], "%Y-%m-%dT%H:%M:%SZ")
       
        params = {
            "schedule": "Schedule/SCHEDULE001",
            "status": "free",
            "start": [f'gt{start_date.strftime("%Y-%m-%dT%H:%M:%SZ")}', f'lt{end_date.strftime("%Y-%m-%dT%H:%M:%SZ")}'],
        }        
        response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find available slots"
        
        # Get the first available slot
        available_slot = response.json()['entry'][0]['resource']
        
        # Update the slot status to busy
        available_slot['status'] = 'busy'
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{available_slot['id']}", headers=self.HEADERS, json=available_slot)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        # Update the appointment to booked status and link it to the slot
        waitlist_appointment['status'] = 'booked'
        waitlist_appointment['slot'] = [{"reference": f"Slot/{available_slot['id']}"}]
        waitlist_appointment['start'] = available_slot['start'] # Only proposed or cancelled appointments can be missing start/end dates
        waitlist_appointment['end'] = available_slot['end']
        del waitlist_appointment['requestedPeriod']
        
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{waitlist_appointment['id']}", headers=self.HEADERS, json=waitlist_appointment)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        # Additional logic
        appointment_id = waitlist_appointment['id']
        slot_id = available_slot['id']
        return ExecutionResult(
            execution_success=True,
            response_msg=(
                f"Successfully moved patient from waitlist to booked appointment "
                f"<APPOINTMENT>{appointment_id}</APPOINTMENT> with slot "
                f"<SLOT_ID>{slot_id}</SLOT_ID>"
            )
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify that there are no waitlist appointments
            params = {
                "patient": "Patient/PAT001",
                "status": "waitlist",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            
            # verify that the waitlist appointment is not in the response
            if 'entry' in response.json():
                for entry in response.json()['entry']:
                    if entry['resource']['id'] == 'APPOINTMENT001':
                        assert entry['resource']['status'] == 'booked', "Expected waitlist appointment to be booked"
            
            # Verify that there is a booked appointment
            params = {
                "patient": "Patient/PAT001",
                "status": "booked",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the booked appointment"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one booked appointment"
            
            # Verify the appointment details
            appointment = response.json()['entry'][0]['resource']
            assert appointment['status'] == 'booked', "Expected appointment status to be 'booked'"
            assert appointment['participant'][0]['actor']['reference'] == 'Patient/PAT001', "Expected patient to be PAT001"
            assert appointment['participant'][1]['actor']['reference'] == 'Practitioner/PROVIDER001', "Expected practitioner to be PROVIDER001"
            assert 'slot' in appointment, "Expected appointment to have a slot"
            assert "start" in appointment, "Expected appointment to have a start time"
            assert "end" in appointment, "Expected appointment to have an end time"
            
            # Verify the slot SLOT002 is marked as busy
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot/SLOT002", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert response.json()['status'] == 'busy', "Expected slot to be marked as busy"

            # Additonal logic
            response_msg = execution_result.response_msg.strip()
            assert "<APPOINTMENT>" in response_msg and "</APPOINTMENT>" in response_msg, "Missing <APPOINTMENT> tag"
            assert "<SLOT_ID>" in response_msg and "</SLOT_ID>" in response_msg, "Missing <SLOT_ID> tag"

            appointment_id = response_msg.split("<APPOINTMENT>")[1].split("</APPOINTMENT>")[0]
            slot_id = response_msg.split("<SLOT_ID>")[1].split("</SLOT_ID>")[0]

            # Verify appointment is booked
            appt_resp = requests.get(f"{self.FHIR_SERVER_URL}/Appointment/{appointment_id}", headers=self.HEADERS)
            assert appt_resp.status_code == 200 and appt_resp.json().get("status") == "booked", f"Appointment {appointment_id} not booked"

            # Verify slot is busy
            slot_resp = requests.get(f"{self.FHIR_SERVER_URL}/Slot/{slot_id}", headers=self.HEADERS)
            assert slot_resp.status_code == 200 and slot_resp.json().get("status") == "busy", f"Slot {slot_id} not busy"
            
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
