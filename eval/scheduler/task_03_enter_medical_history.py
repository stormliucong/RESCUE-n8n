# task_03_enter_medical_history.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class EnterMedicalHistoryTask(TaskInterface):
    def get_task_id(self) -> str:
        return "3"

    def get_task_name(self) -> str:
        return "Enter Medical History"

    def get_prompt(self) -> str:
        return """
Task: Record a medical condition

Record a medical condition for the patient id=PAT001 in his medical history that he has a hypertension. 
Using SNOMED CT (http://snomed.info/sct) for coding.
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "1990-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        condition_data = {
            "resourceType": "Condition",
            "subject": { "reference": "Patient/PAT001" },
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension"
                }],
                "text": "Hypertension"
            },
            "clinicalStatus": { "coding": [{ "code": "active" }] }
        }

        response = requests.post(
            f"{self.FHIR_SERVER_URL}/Condition",
            headers=self.HEADERS,
            json=condition_data
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
            
            response_json = response.json()
            assert response_json.get("resourceType") == "Condition", "Resource type must be Condition"
            assert response_json.get("subject", {}).get("reference") == "Patient/PAT001", "Subject reference must be Patient/PAT001"
            
            coding = response_json.get("code", {}).get("coding", [{}])[0]
            assert coding.get("system") == "http://snomed.info/sct", "Coding system must be SNOMED CT"
            assert coding.get("code") == "38341003", "Incorrect SNOMED code for hypertension"

            return TaskResult(
                success=True,
                error_message=None,
                response_data=response_json
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
    
    task = EnterMedicalHistoryTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)