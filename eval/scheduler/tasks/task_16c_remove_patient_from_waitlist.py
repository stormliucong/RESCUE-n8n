import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class RemovePatientFromWaitlistTask(TaskInterface):
    def get_task_id(self) -> str:
        return "16c"

    def get_task_name(self) -> str:
        return "Remove Patient From Waitlist"

    def get_prompt(self) -> str:
        return """
Task: Patient John Doe (PAT001) no longer wants to be on the waitlist. Remove them from the waitlist.

After removal, return the cancelled appointment ID using the following format:
<APPOINTMENT>appointment_id</APPOINTMENT>
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
                            "schedule": {"reference": "Schedule/SCHEDULE001"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": status
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

            # Create a waitlist appointment
            start = datetime.now() + timedelta(days=1)
            end = datetime.now() + timedelta(days=6)
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
        
        # Update the appointment status to cancelled
        waitlist_appointment['status'] = 'cancelled'
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{waitlist_appointment['id']}", headers=self.HEADERS, json=waitlist_appointment)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        appointment_id = waitlist_appointment['id']
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Successfully removed patient from waitlist by cancelling appointment <APPOINTMENT>{appointment_id}</APPOINTMENT>"
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
            # bug in HAPI FHIR server, cancelled appointments are also returned
            # so we need to filter them out
            appointments = response.json()
            if 'entry' in appointments:
                appointments['entry'] = [entry for entry in response.json()['entry'] if entry['resource']['status'] == 'waitlist']
            assert 'entry' not in appointments or len(appointments['entry']) == 0, "Expected no waitlist appointments"
            
            # Verify that the appointment is cancelled
            params = {
                "patient": "Patient/PAT001",
                "status": "cancelled",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the cancelled appointment"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one cancelled appointment"
            
            # Verify the appointment details
            appointment = response.json()['entry'][0]['resource']
            assert appointment['status'] == 'cancelled', "Expected appointment status to be 'cancelled'"
            assert appointment['participant'][0]['actor']['reference'] == 'Patient/PAT001', "Expected patient to be PAT001"
            assert appointment['participant'][1]['actor']['reference'] == 'Practitioner/PROVIDER001', "Expected practitioner to be PROVIDER001"

            # Added logic
            response_msg = execution_result.response_msg.strip()
            assert "<APPOINTMENT>" in response_msg and "</APPOINTMENT>" in response_msg, "Missing <APPOINTMENT> tag"
            appointment_id = response_msg.split("<APPOINTMENT>")[1].split("</APPOINTMENT>")[0]

            # Verify the Appointment resource is cancelled
            appt_resp = requests.get(f"{self.FHIR_SERVER_URL}/Appointment/{appointment_id}", headers=self.HEADERS)
            assert appt_resp.status_code == 200 and appt_resp.json().get("status") == "cancelled", f"Appointment {appointment_id} not cancelled"

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
            {"getAllResources": 0, "updateResource": 1},
            {"getAllResources": 0, "deleteResource": 1},
            {"getResourceById": 0, "updateResource": 1},
            {"getResourceById": 0, "deleteResource": 1}
        ]

    def get_required_resource_types(self) -> list:
        return ["Appointment"]

    def get_prohibited_tools(self) -> list:
        return ["createResource"]

    def get_difficulty_level(self) -> int:
        return 2