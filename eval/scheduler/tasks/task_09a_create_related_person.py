# task_09a_create_related_person.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

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

After creation, return the new RelatedPerson ID using the following format: <RELATED_PERSON>related_person_id</RELATED_PERSON>

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



    def execute_human_agent(self) -> ExecutionResult:
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
        
        if response.status_code != 201:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to create related person: {response.text}"
            )

        response_json = response.json()
        related_person_id = response_json.get('id')
        return ExecutionResult(
            execution_success=True,
            response_msg=f"Created related person with ID <RELATED_PERSON>{related_person_id}</RELATED_PERSON>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the related person was created correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/RelatedPerson",
                headers=self.HEADERS,
                params={"patient": "Patient/PAT001"}
            )
            
            assert response.status_code in [200, 201], f"Expected status code 200 or 201, got {response.status_code}"
            
            response_json = response.json()
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one related person"
            
            related_person = response_json['entry'][0]['resource']
            assert related_person["resourceType"] == "RelatedPerson", "Invalid resource type"
            assert related_person["patient"]["reference"] == "Patient/PAT001", "Invalid patient reference"
            assert related_person["birthDate"] == "1960-03-01", "Invalid birth date"
            assert related_person["name"][0]["family"] == "Doe", "Invalid family name"
            assert "Alice" in related_person["name"][0]["given"], "Invalid given name"
        

            # Additional asserts
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<RELATED_PERSON>" in response_msg, "Expected to find <RELATED_PERSON> tag"
            assert "</RELATED_PERSON>" in response_msg, "Expected to find </RELATED_PERSON> tag"
            related_person_id = response_msg.split("<RELATED_PERSON>")[1].split("</RELATED_PERSON>")[0]
            assert related_person_id is not None, "Expected to find related_person_id"
            
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

    # def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
    #     # This method will be implemented with detailed failure mode analysis later
    #     return TaskFailureMode(
    #         incorrect_tool_selection=False,
    #         incorrect_tool_order=False,
    #         incorrect_resource_type=False,
    #         error_codes=None
    #     )

    def get_required_tool_call_sets(self) -> list:
        return [
            {"createResource": 0},
            {"getAllResources": 0, "createResource": 1},
            {"getAllResources": 0, "deleteResource": 1, "createResource": 2},
            {"getAllResources": 0, "updateResource": 1},
            {"getResourceById": 0, "updateResource": 1},
            {"getResourceById": 0, "createResource": 1}
        ]

    def get_required_resource_types(self) -> list:
        return ["RelatedPerson"]

    def get_prohibited_tools(self) -> list:
        return []

    def get_difficulty_level(self) -> int:
        return 1
