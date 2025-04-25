# task_09a_create_related_person.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class CreateRelatedPersonTask(TaskInterface):
    def get_task_id(self) -> str:
        return "9a"

    def get_task_name(self) -> str:
        return "Create Related Person"

    def get_prompt(self) -> str:
        return """
Task: Create a related person resource

Create a related person resource for the patient PAT001 with the following details:
- Name: Alice Doe
- Relationship: Mother
- Date of Birth: March 1, 1960
"""

    def prepare_test_data(self) -> None:
        try:
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "2010-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        related_person_payload = {
            "resourceType": "RelatedPerson",
            "patient": {"reference": "Patient/PAT001"},
            "relationship": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "MOTHER"
                }],
                "text": "mother"
            }],
            "name": [{"use": "official", "family": "Doe", "given": ["Alice"]}],
            "gender": "female",
            "birthDate": "1960-03-01"
        }
        
        response = requests.post(
            f"{self.FHIR_SERVER_URL}/RelatedPerson",
            headers=self.HEADERS,
            json=related_person_payload
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
            
            response_json = response.json()
            assert response_json["resourceType"] == "RelatedPerson", "Invalid resource type"
            assert response_json["patient"]["reference"] == "Patient/PAT001", "Invalid patient reference"
            assert response_json["birthDate"] == "1960-03-01", "Invalid birth date"
            assert response_json["name"][0]["family"] == "Doe", "Invalid family name"
            assert "Alice" in response_json["name"][0]["given"], "Invalid given name"
            
            relationship = response_json["relationship"][0]
            assert relationship["coding"][0]["code"] == "MOTHER", "Invalid relationship code"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "related_person": response_json,
                    "relationship": relationship
                }
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
    
    task = CreateRelatedPersonTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)