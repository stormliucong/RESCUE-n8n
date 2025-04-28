# task_14a_make_appointment_1.py
import os
import time
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult

class MakeAppointmentTask(TaskInterface):
    def get_task_id(self) -> str:
        return "14a"

    def get_task_name(self) -> str:
        return "Make Appointment 1"

    def get_prompt(self) -> str:
        return """
Task: Make an appointment time for the patient John Doe with Provider Dr. John Smith on next Monday morning at 9am."
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

    def execute_human_agent(self) -> Dict:
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
        response = requests.put(f"{FHIR_SERVER_URL}/Appointment/APPOINTMENT001", headers=self.HEADERS, json=params)
        assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response body: {response.text}"
        params = {
            "resourceType": "Slot",
            "id": "SLOT001",
            "status": "busy",
        }
        response = requests.put(f"{FHIR_SERVER_URL}/Slot/SLOT001", headers=self.HEADERS, json=params)
        assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"

        return response
        

    def validate_response(self) -> TaskResult:
        try:
            start = datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)
            start = start.replace(hour=9, minute=0, second=0, microsecond=0)
            # query appointment reference to slot1
            params = {
                "practitioner": "Practitioner/PROVIDER001",
                "date": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            response = requests.get(f"{FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
            # check the participant is correct
            assert 'entry' in response.json(), "Expected entry in the response"
            assert len(response.json()['entry']) == 1, "Expected one appointment" 
            assert response.json()['entry'][0]['resource']['participant'][0]['actor']['reference'] == "Patient/PAT001", "Expected patient reference to be PAT001"
            assert response.json()['entry'][0]['resource']['participant'][1]['actor']['reference'] == "Practitioner/PROVIDER001", "Expected practitioner reference to be PROVIDER001"
            # check the slot reference is busy
            slot_id = response.json()['entry'][0]['resource']['slot'][0]['reference']
            response = requests.get(f"{FHIR_SERVER_URL}/{slot_id}", headers=self.HEADERS)
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            assert response.json()['status'] == "busy", "Expected slot to be busy"
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
    
    task = MakeAppointmentTask(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response()
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
    
    
    
    