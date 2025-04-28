# task_14a_make_appointment_1.py

import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class CancelAppointmentTask(TaskInterface):
    def get_task_id(self) -> str:
        return "15a"

    def get_task_name(self) -> str:
        return "Cancel Next Appointment"

    def get_prompt(self) -> str:
        return """
Task: Cancel Patient John Doe's next coming appointment.
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
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(appointment1)

            # Create a second appointment for the same patient on Tuesday
            start = start + timedelta(days=1)
            slot2 = {
                "resourceType": "Slot",
                "id": "SLOT002",
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            self.upsert_to_fhir(appointment2)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        # Find the next appointment for John Doe
        params = {
            "patient": "Patient/PAT001",
            "status": "booked",
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find at least one appointment"
        
        # Find the appointment with the earliest start date
        appointment_to_cancel = None
        earliest_start_date = datetime.max
        for appointment in response.json()['entry']:
            slot = appointment['resource']['slot'][0]['reference']
            slot_response = requests.get(f"{self.FHIR_SERVER_URL}/{slot}", headers=self.HEADERS)
            assert slot_response.status_code == 200, f"Expected status code 200, but got {slot_response.status_code}. Response body: {slot_response.text}"
            start_date = slot_response.json()['start']
            if datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ") < earliest_start_date:
                earliest_start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
                appointment_to_cancel = appointment

        assert appointment_to_cancel is not None, "Expected to find an appointment to cancel"
        
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
            "start": earliest_start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": (earliest_start_date + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schedule": {"reference": "Schedule/SCHEDULE001"},
        }
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{slot_id}", headers=self.HEADERS, json=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        return response

    def validate_response(self) -> TaskResult:
        try:
            # Verify that the earliest appointment is cancelled
            params = {
                "patient": "Patient/PAT001",
                "status": "cancelled",
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the cancelled appointment"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one cancelled appointment"
            
            # Verify that the slot is now free
            slot_id = response.json()['entry'][0]['resource']['slot'][0]['reference']
            response = requests.get(f"{self.FHIR_SERVER_URL}/{slot_id}", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert response.json()['status'] == "free", "Expected slot to be free after cancellation"

            return TaskResult(
                success=True,
                error_message=None,
                response_data=response.json()
            )
        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response.json() if hasattr(response, 'json') else None
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_data=response.json() if hasattr(response, 'json') else None
            )

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = CancelAppointmentTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response()
    print(eval_results) 