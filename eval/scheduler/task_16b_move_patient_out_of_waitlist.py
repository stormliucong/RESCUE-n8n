import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class MovePatientOutOfWaitlistTask(TaskInterface):
    def get_task_id(self) -> str:
        return "16b"

    def get_task_name(self) -> str:
        return "Move Patient Out of Waitlist"

    def get_prompt(self) -> str:
        return """
Task: Move patient John Doe (PAT001) out of the waitlist by booking them into an available slot with Dr. Smith.
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

    def execute_human_agent(self) -> Dict:
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
        waitlist_appointment['start'] = available_slot['start']
        waitlist_appointment['end'] = available_slot['end']
        del waitlist_appointment['requestedPeriod']
        
        response = requests.put(f"{self.FHIR_SERVER_URL}/Appointment/{waitlist_appointment['id']}", headers=self.HEADERS, json=waitlist_appointment)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
        
        return response.json()

    def validate_response(self) -> TaskResult:
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
            
            # Verify the slot SLOT002 is marked as busy
            response = requests.get(f"{self.FHIR_SERVER_URL}/Slot/SLOT002", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert response.json()['status'] == 'busy', "Expected slot to be marked as busy"
            
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
    
    task = MovePatientOutOfWaitlistTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response()
    print(eval_results) 