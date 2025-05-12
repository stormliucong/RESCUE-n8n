# task_13a_find_patient_from_slot_1.py
import os
import requests
from typing import Dict, Any
from datetime import datetime, timedelta
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class FindPatientFromSlotTask(TaskInterface):
    def get_task_id(self) -> str:
        return "13a"

    def get_task_name(self) -> str:
        return "Find Patient From Slot - Dr. John Smith"

    def get_prompt(self) -> str:
        return """
Task: Find the patient who has booked Dr. John Smith's slots next Monday morning at 9am.

After finding, return the patient ID using the following format: <PATIENT_ID>patient_id</PATIENT_ID>
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
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "participant": [{"actor": {"reference": "Patient/PAT001"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER001"}, "status": "accepted"}],
            }
            self.upsert_to_fhir(appointment1)


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
                "status": "busy",
                "schedule": {"reference": "Schedule/SCHEDULE002"},
            }
            self.upsert_to_fhir(slot2)
            appointment2 = {
                "resourceType": "Appointment",
                "id": "APPOINTMENT002",
                "status": "booked",
                "slot": [{"reference": "Slot/SLOT002"}],
                "start": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end": (start + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "participant": [{"actor": {"reference": "Patient/PAT002"}, "status": "accepted"}, {"actor": {"reference": "Practitioner/PROVIDER002"}, "status": "accepted"}],
            }
            self.upsert_to_fhir(appointment2)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        # Find next Monday's slot at 9am
        next_monday = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
        target_time = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        params={
                "start": target_time.strftime("%Y-%m-%d"),
                "schedule.actor.given": "John",
                "schedule.actor.family": "Smith",
        }
        response = requests.get(f"{self.FHIR_SERVER_URL}/Slot", headers=self.HEADERS, params=params)
        if 'entry' not in response.json():
            return ExecutionResult(
                execution_success=False,
                response_msg="No slots found for Dr. John Smith"
            )
        slot_id = response.json()['entry'][0]['resource']['id']
        params = {"slot": f"Slot/{slot_id}"}
        response = requests.get(f"{self.FHIR_SERVER_URL}/Appointment", headers=self.HEADERS, params=params)
        patient_id = response.json()['entry'][0]['resource']['participant'][0]['actor']['reference']
        response = requests.get(f"{self.FHIR_SERVER_URL}/{patient_id}", headers=self.HEADERS)

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Successfully found patient <PATIENT_ID>{patient_id}</PATIENT_ID> for Dr. John Smith's slot"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<PATIENT_ID>" in response_msg, "Expected to find <PATIENT_ID> tag"
            assert "</PATIENT_ID>" in response_msg, "Expected to find </PATIENT_ID> tag"
            patient_id = response_msg.split("<PATIENT_ID>")[1].split("</PATIENT_ID>")[0]
            expected_id = self.execute_human_agent().response_msg.split("<PATIENT_ID>")[1].split("</PATIENT_ID>")[0]
            assert patient_id == expected_id, f"Expected patient_id {expected_id}, got {patient_id}"
            
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

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = FindPatientFromSlotTask(FHIR_SERVER_URL, N8N_URL)
    
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
        