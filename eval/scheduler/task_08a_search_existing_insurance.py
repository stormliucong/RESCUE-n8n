# task_08a_search_existing_insurance.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

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

If found, return the coverage ID using the following format: <COVERAGE>coverage_id</COVERAGE>
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


    def execute_human_agent(self) -> ExecutionResult:
        params = {
            "beneficiary": "Patient/PAT001",
            "status": "active"
        }

        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Coverage",
            headers=self.HEADERS,
            params=params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for insurance: {response.text}"
            )

        response_json = response.json()
        coverage_id = response_json['entry'][0]['resource']['id']

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found {response_json.get('total', 0)} insurance coverage(s) for patient PAT001: <COVERAGE>{coverage_id}</COVERAGE>"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the insurance coverage was found correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Coverage",
                headers=self.HEADERS,
                params={"beneficiary": "Patient/PAT001", "status": "active"}
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            #assert response_json['total'] >= 1, f"Expected at least one insurance, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) >= 1, f"Expected at least one insurance, but got {len(response_json['entry'])}"

            # Validate coverage details
            coverage = response_json['entry'][0]['resource']
            assert coverage['resourceType'] == "Coverage", "Resource type must be Coverage"
            assert coverage['beneficiary']['reference'] == "Patient/PAT001", "Beneficiary reference must be Patient/PAT001"
            assert coverage['status'] == "active", "Coverage must be active"


            # Structured-output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<COVERAGE>" in response_msg, "Expected to find <COVERAGE> tag"
            assert "</COVERAGE>" in response_msg, "Expected to find </COVERAGE> tag"
            coverage_id = response_msg.split("<COVERAGE>")[1].split("</COVERAGE>")[0]
            expected_id = self.execute_human_agent().response_msg.split("<COVERAGE>")[1].split("</COVERAGE>")[0]
            assert coverage_id == expected_id, f"Expected coverage_id {expected_id}, got {coverage_id}"
            # Cross-check with FHIR response
            coverage_resource = response_json['entry'][0]['resource']
            assert coverage_resource['id'] == coverage_id, f"Expected FHIR coverage id {coverage_id}, got {coverage_resource['id']}"


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

