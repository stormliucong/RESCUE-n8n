# task_07_enter_insurance.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class EnterInsuranceTask(TaskInterface):
    def get_task_id(self) -> str:
        return "7"

    def get_task_name(self) -> str:
        return "Enter Insurance"

    def get_prompt(self) -> str:
        return """
Task: Add insurance information for a patient
   - Insurance provider: Acme Health Insurance
   - Policy period: January 1, 2024 to December 31, 2025
   - Subscriber and policy holder: patient's father
   - Group Plan: Employer Group Plan (Group ID: Group-98765)
   - Plan ID: GOLD123
"""

    def prepare_test_data(self) -> None:
        try:
            # Create test patient
            patient_resource = {
                "resourceType": "Patient",
                "id": "PAT001",
                "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                "birthDate": "2010-06-15",
                "telecom": [{"system": "phone", "value": "123-456-7890"}],
                "address": [{"line": ["123 Main St"], "city": "Boston", "state": "MA"}]
            }
            self.upsert_to_fhir(patient_resource)

            # Create insurance organization
            organization_resource = {
                "resourceType": "Organization",
                "id": "ORG-INSURER001",
                "name": "Acme Health Insurance"
            }
            self.upsert_to_fhir(organization_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        try:
            # Step 1: Create RelatedPerson (father)
            related_person_payload = {
                "resourceType": "RelatedPerson",
                "patient": {"reference": "Patient/PAT001"},
                "relationship": [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-RoleCode',
                        'code': 'FATHER'
                    }]
                }]
            }
            
            related_person_response = requests.post(
                f"{self.FHIR_SERVER_URL}/RelatedPerson",
                headers=self.HEADERS,
                json=related_person_payload
            )
            related_person_id = related_person_response.json()['id']

            # Step 2: Find insurance organization
            org_params = {"name": "Acme Health Insurance"}
            org_response = requests.get(
                f"{self.FHIR_SERVER_URL}/Organization",
                headers=self.HEADERS,
                params=org_params
            )

            # Step 3: Create Coverage
            coverage_payload = {
                'resourceType': 'Coverage',
                'status': 'active',
                'kind': {
                    'coding': [{
                        'system': 'http://hl7.org/fhir/coverage-kind',
                        'code': 'insurance'
                    }]
                },
                'subscriber': {'reference': f'RelatedPerson/{related_person_id}'},
                'beneficiary': {'reference': 'Patient/PAT001'},
                'insurer': {'reference': 'Organization/ORG-INSURER001'},
                'period': {'start': '2024-01-01', 'end': '2025-12-31'},
                'class': [
                    {
                        'type': {
                            'coding': [{
                                'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html',
                                'code': 'group'
                            }]
                        },
                        'value': 'Group-98765'
                    },
                    {
                        'type': {
                            'coding': [{
                                'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html',
                                'code': 'plan'
                            }]
                        },
                        'value': 'Plan-GOLD123'
                    }
                ]
            }
            
            coverage_response = requests.post(
                f"{self.FHIR_SERVER_URL}/Coverage",
                headers=self.HEADERS,
                json=coverage_payload
            )

            return {
                "related_person": related_person_response,
                "organization": org_response,
                "coverage": coverage_response
            }

        except Exception as e:
            raise Exception(f"Failed to execute task: {str(e)}")

    def validate_response(self, response: Dict[str, Any]) -> TaskResult:
        try:
            # Validate RelatedPerson creation
            related_person_response = response["related_person"]
            assert related_person_response.status_code == 201, f"Expected status code 201 for RelatedPerson, got {related_person_response.status_code}"
            related_person_json = related_person_response.json()
            assert related_person_json["resourceType"] == "RelatedPerson", "Invalid resource type for RelatedPerson"
            assert related_person_json["patient"]["reference"] == "Patient/PAT001", "Invalid patient reference in RelatedPerson"

            # Validate Organization search
            org_response = response["organization"]
            assert org_response.status_code == 200, f"Expected status code 200 for Organization search, got {org_response.status_code}"
            org_json = org_response.json()
            assert org_json["total"] >= 1, "Organization not found"
            assert org_json["entry"][0]["resource"]["name"] == "Acme Health Insurance", "Invalid organization name"

            # Validate Coverage creation
            coverage_response = response["coverage"]
            assert coverage_response.status_code == 201, f"Expected status code 201 for Coverage, got {coverage_response.status_code}"
            coverage_json = coverage_response.json()
            assert coverage_json["resourceType"] == "Coverage", "Invalid resource type for Coverage"
            assert coverage_json["status"] == "active", "Coverage status should be active"
            assert coverage_json["period"]["start"] == "2024-01-01", "Invalid coverage start date"
            assert coverage_json["period"]["end"] == "2025-12-31", "Invalid coverage end date"
            
            # Validate Coverage details
            found_group = False
            found_plan = False
            for class_item in coverage_json["class"]:
                if class_item["value"] == "Group-98765":
                    found_group = True
                elif class_item["value"] == "Plan-GOLD123":
                    found_plan = True
            assert found_group, "Group ID not found in coverage"
            assert found_plan, "Plan ID not found in coverage"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "related_person": related_person_response.json(),
                    "organization": org_response.json(),
                    "coverage": coverage_response.json()
                }
            )

        except AssertionError as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                response_data=response
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                response_data=response
            )

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
    N8N_URL = os.getenv("N8N_AGENT_URL")
    
    task = EnterInsuranceTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)