# task_17b_reschedule_with_another_provider.py
import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class RescheduleWithAnotherProviderTask(TaskInterface):
    def get_task_id(self) -> str:
        return "17b"

    def get_task_name(self) -> str:
        return "Reschedule Appointment with Another Provider"

    def get_prompt(self) -> str:
        return """
Task: Reschedule John Doe's (PAT001) appointment with another provider who has availability at the same time.
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

            # Create first practitioner (current provider)
            practitioner1 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER001",
                "name": [{"use": "official", "family": "Smith", "given": ["John"]}],
                "gender": "male",
                "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
                "address": [{"use" : "work", "line": ["123 Main St"], "city": "Boston", "state": "MA"}],
            }
            self.upsert_to_fhir(practitioner1)

            # Create second practitioner (new provider)
            practitioner2 = {
                "resourceType": "Practitioner",
                "id": "PROVIDER002",
                "name": [{"use": "official", "family": "Johnson", "given": ["Jane"]}],
                "gender": "female",
                "communication": [{"coding": [{"system": "urn:ietf:bcp:47", "code": "en"}]}],
                "address": [{"use" : "work", "line": ["456 Oak St"], "city": "Boston", "state": "MA"}],
            }
            self.upsert_to_fhir(practitioner2)

            # Create schedule for first practitioner
            start = datetime.now()
            end = start + timedelta(days=14)
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

            # Create schedule for second practitioner
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

            # Create slots for first practitioner (all busy)
            j = 1
            for x in range(14):
                for i in range(9, 12):  # Morning hours only
                    if datetime.now().weekday() < 5:  # Weekdays only
                        start_time = datetime.now() + timedelta(days=x)
                        start_time = start_time.replace(hour=i, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)
                        
                        slot = {
                            "resourceType": "Slot",
                            "id": f"SLOT00{j}",
                            "schedule": {"reference": "Schedule/SCHEDULE001"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": "busy"
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

            # Create slots for second practitioner (all free)
            for x in range(14):
                for i in range(9, 12):  # Morning hours only
                    if datetime.now().weekday() < 5:  # Weekdays only
                        start_time = datetime.now() + timedelta(days=x)
                        start_time = start_time.replace(hour=i, minute=0, second=0, microsecond=0)
                        end_time = start_time + timedelta(hours=1)
                        
                        slot = {
                            "resourceType": "Slot",
                            "id": f"SLOT{j}",
                            "schedule": {"reference": "Schedule/SCHEDULE002"},
                            "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "status": "free"
                        }
                        self.upsert_to_fhir(slot)
                        j += 1

            # Create current appointment with first practitioner at next Monday at 9am
            start_time = datetime.now() + timedelta((7 - datetime.now().weekday()) % 7)
            start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            # Find current slot with first practitioner at next Monday at 9am
            params = {
                "schedule": "Schedule/SCHEDULE001",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            current_slot = response.json()['entry'][0]['resource']
            current_slot_id = current_slot['id']

            # First provider declines the appointment
            current_appointment = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT001",
                "status": "proposed",
                "slot": [{"reference": f"Slot/{current_slot_id}"}],
                "participant": [
                    {"actor": {"reference": "Patient/PAT001"}, "status": "accepted"},
                    {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "declined"}
                ],
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
            self.upsert_to_fhir(current_appointment)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        # Find the current appointment
        start_time = datetime.now() + timedelta((7 - datetime.now().weekday()) % 7)
        start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        
        params = {
            "patient": "Patient/PAT001",
            "date": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find the current appointment"
        assert len(response.json()['entry']) == 1, "Expected to find exactly one appointment"
        current_appointment = [entry['resource'] for entry in response.json()['entry']][0]
        current_slot_start = current_appointment['start']
        
        # Find an available slot with the second practitioner at the same time
        params = {
            "schedule": "Schedule/SCHEDULE002",
            "status": "free",
            "start": current_slot_start,
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        assert 'entry' in response.json(), "Expected to find available slots"
        assert len(response.json()['entry']) == 1, "Expected to find exactly one available slot"
        new_slot = response.json()['entry'][0]['resource']
        
        # Leave the current slot unchanged
               
        # Update the new slot to busy
        new_slot['status'] = 'busy'
        response = requests.put(f"{self.FHIR_SERVER_URL}/Slot/{new_slot['id']}", headers=self.HEADERS, json=new_slot)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        # Update the appointment to the new slot and practitioner
        current_appointment['slot'] = [{"reference": f"Slot/{new_slot['id']}"}]
        current_appointment['start'] = new_slot['start']
        current_appointment['end'] = new_slot['end']
        current_appointment['participant'][1]['actor']['reference'] = "Practitioner/PROVIDER002"
        current_appointment['participant'][1]['actor']['status'] = "accepted"
        current_appointment['status'] = 'booked'
        
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{current_appointment['id']}", headers=self.HEADERS, json=current_appointment)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        return response.json()

    def validate_response(self) -> TaskResult:
        try:
            # Verify that the current slot is still busy
            start_time = datetime.now() + timedelta((7 - datetime.now().weekday()) % 7)
            start_time = start_time.replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
            
            params = {
                "schedule": "Schedule/SCHEDULE001",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the current slot"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one slot"
            current_slot = response.json()['entry'][0]['resource']
            assert current_slot['status'] == 'busy', "Expected current slot to be busy"
            
            # Verify that the new slot is busy
            params = {
                "schedule": "Schedule/SCHEDULE002",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the busy slot"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one busy slot"
            new_slot = response.json()['entry'][0]['resource']
            assert new_slot['status'] == 'busy', "Expected new slot to be busy"
            
            
            # Verify the appointment details
            params = {
                "patient": "Patient/PAT001",
                "status": "booked",
                "date": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert 'entry' in response.json(), "Expected to find the appointment"
            assert len(response.json()['entry']) == 1, "Expected to find exactly one appointment"
            # HAPI FHIR server returns cancelled appointments, so we need to filter them out
            appointment = [entry['resource'] for entry in response.json()['entry'] if entry['resource']['status'] == 'booked'][0]
            assert appointment['status'] == 'booked', "Expected appointment status to be 'booked'"
            assert appointment['participant'][0]['actor']['reference'] == 'Patient/PAT001', "Expected patient to be PAT001"
            assert appointment['participant'][1]['actor']['reference'] == 'Practitioner/PROVIDER002', "Expected practitioner to be PROVIDER002"

            # Verify the appointment is with the new slot
            assert appointment['slot'][0]['reference'] == f"Slot/{new_slot['id']}", "Expected slot to be the new slot"
           
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
    
    task = RescheduleWithAnotherProviderTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response()
    print(eval_results) 