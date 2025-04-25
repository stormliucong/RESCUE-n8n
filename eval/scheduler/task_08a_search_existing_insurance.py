# task_08a_search_existing_insurance.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult

class SearchExistingInsuranceTask(TaskInterface):
    def get_task_id(self) -> str:
        return "8a"

    def get_task_name(self) -> str:
        return "Search Existing Insurance"

    def get_prompt(self) -> str:
        return """
Task: Search for patient insurance information

Search if patient insurance information has been entered in the system for:
- Beneficiary: John Doe (id=PAT001)
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

            # Create related person
            related_person_resource = {
                "resourceType": "RelatedPerson",
                "id": "PAT001-FATHER",
                "patient": {"reference": "Patient/PAT001"},
            }
            self.upsert_to_fhir(related_person_resource)

            # Create coverage
            coverage_resource = {
                'resourceType': 'Coverage',
                'id': 'COV-PAT001',
                'status': 'active',
                'kind': {'coding': [{'system': 'http://hl7.org/fhir/coverage-kind', 'code': 'insurance'}]},
                'subscriber': {'reference': 'RelatedPerson/PAT001-FATHER'},
                'beneficiary': {'reference': 'Patient/PAT001'},
                'insurer': {'reference': 'Organization/ORG-INSURER001'},
                'period': {'start': '2024-01-01', 'end': '2025-12-31'},
                'class': [
                    {
                        'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'group'}]},
                        'value': 'Group-98765'
                    },
                    {
                        'type': {'coding': [{'system': 'https://terminology.hl7.org/6.2.0/CodeSystem-coverage-class.html', 'code': 'plan'}]},
                        'value': 'Plan-GOLD123'
                    }
                ]
            }
            self.upsert_to_fhir(coverage_resource)
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")

    def execute_human_agent(self) -> Dict:
        params = {
            "beneficiary": "Patient/PAT001",
            "status": "active"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Coverage",
            headers=self.HEADERS,
            params=params
        )
        
        return response

    def validate_response(self, response: Any) -> TaskResult:
        try:
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] >= 1, f"Expected at least one insurance, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) >= 1, f"Expected at least one insurance, but got {len(response_json['entry'])}"

            # Validate coverage details
            coverage = response_json['entry'][0]['resource']
            assert coverage['resourceType'] == "Coverage", "Resource type must be Coverage"
            assert coverage['beneficiary']['reference'] == "Patient/PAT001", "Beneficiary reference must be Patient/PAT001"
            assert coverage['status'] == "active", "Coverage must be active"

            return TaskResult(
                success=True,
                error_message=None,
                response_data={
                    "coverages_found": response_json['total'],
                    "coverage_details": coverage
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
    
    task = SearchExistingInsuranceTask(FHIR_SERVER_URL, N8N_URL)
    print(task.get_task_id())
    print(task.get_task_name())
    task.cleanup_test_data()
    task.prepare_test_data()
    human_response = task.execute_human_agent()
    eval_results = task.validate_response(human_response)
    print(eval_results)
    # n8n_response = task.execute_n8n_agent()
    # print(n8n_response)
