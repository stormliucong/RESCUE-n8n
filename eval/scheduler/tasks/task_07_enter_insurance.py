# task_07_enter_insurance.py
import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class EnterInsuranceTask(TaskInterface):
    def get_task_id(self) -> str:
        return "7"

    def get_task_name(self) -> str:
        return "Enter Insurance"

    def get_prompt(self) -> str:
        return """
Task: Add insurance information for a patient PAT001
   - Insurance provider: Acme Health Insurance
   - Policy period: January 1, 2024 to December 31, 2025
   - Subscriber and policy holder: patient's father
   - Group Plan: Employer Group Plan (Group ID: Group-98765)
   - Plan ID: GOLD123

After creating the coverage, return the newly created Coverage ID using the following format: <COVERAGE>coverage_id</COVERAGE>

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


    def execute_human_agent(self) -> ExecutionResult:
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
            
            if related_person_response.status_code != 201:
                return ExecutionResult(
                    execution_success=False,
                    response_msg=f"Failed to create related person: {related_person_response.text}"
                )
            
            related_person_id = related_person_response.json()['id']

            # Step 2: Find insurance organization
            org_params = {"name": "Acme Health Insurance"}
            org_response = requests.get(
                f"{self.FHIR_SERVER_URL}/Organization",
                headers=self.HEADERS,
                params=org_params
            )
            
            if org_response.status_code != 200:
                return ExecutionResult(
                    execution_success=False,
                    response_msg=f"Failed to find insurance organization: {org_response.text}"
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
            
            if coverage_response.status_code != 201:
                return ExecutionResult(
                    execution_success=False,
                    response_msg=f"Failed to create coverage: {coverage_response.text}"
                )
        
            coverage_id = coverage_response.json().get('id')
            return ExecutionResult(
                execution_success=True,
                response_msg=f"Successfully created insurance coverage with ID <COVERAGE>{coverage_id}</COVERAGE>"
            )

        except Exception as e:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to execute task: {str(e)}"
            )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the insurance coverage was created correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Coverage",
                headers=self.HEADERS,
                params={"beneficiary": "Patient/PAT001", "status": "active"}
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] >= 1, f"Expected at least one insurance, but got {response_json['total']}"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) >= 1, f"Expected at least one insurance, but got {len(response_json['entry'])}"

            # Validate coverage details
            coverage = response_json['entry'][0]['resource']
            assert coverage['resourceType'] == "Coverage", "Resource type must be Coverage"
            assert coverage['status'] == "active", "Coverage must be active"
            assert coverage['beneficiary']['reference'] == "Patient/PAT001", "Invalid beneficiary reference"
            assert coverage['insurer']['reference'] == "Organization/ORG-INSURER001", "Invalid insurer reference"   
            # Validate coverage class details
            found_group = False
            found_plan = False
            for class_item in coverage['class']:
                if class_item['value'] == "Group-98765":
                    found_group = True
                elif class_item['value'] == "Plan-GOLD123":
                    found_plan = True
            assert found_group, "Group ID not found in coverage"
            assert found_plan, "Plan ID not found in coverage"

            # Additional eval logic
            # Structured‐output assertions
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            response_msg = response_msg.strip()
            assert "<COVERAGE>" in response_msg, "Expected to find <COVERAGE> tag"
            assert "</COVERAGE>" in response_msg, "Expected to find </COVERAGE> tag"
            coverage_id = response_msg.split("<COVERAGE>")[1].split("</COVERAGE>")[0]
            assert coverage_id is not None, "Expected to find coverage_id"

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