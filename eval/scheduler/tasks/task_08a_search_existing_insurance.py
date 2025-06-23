# task_08a_search_existing_insurance.py
import os
import time
<<<<<<< HEAD
import time
=======
>>>>>>> b817ea0b219028ffc44e9549f23a2cf0983af377
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
Task: Search for patient (id=PAT001) insurance information

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
<<<<<<< HEAD
            self.upsert_to_fhir(coverage_resource)
            #resp = self.upsert_to_fhir(coverage_resource)
            # if resp:                                # only non-None on failure
            #     print("Coverage upsert failed: %s %s",
            #                 resp.status_code, resp.text)
            #     raise RuntimeError("Failed to create coverage")
=======
            resp = self.upsert_to_fhir(coverage_resource)
            if resp:                                # only non-None on failure
                print("Coverage upsert failed: %s %s",
                            resp.status_code, resp.text)
                raise RuntimeError("Failed to create coverage")
>>>>>>> b817ea0b219028ffc44e9549f23a2cf0983af377
            
            # TEST
            # Testing POLL to wait for the server to finish indexing..
            self.poll_until_exists('Patient', 'PAT001')
            self.poll_until_exists('Organization', 'ORG-INSURER001')
            self.poll_until_exists('RelatedPerson', 'PAT001-FATHER')
            self.poll_until_exists('Coverage', 'COV-PAT001')

            time.sleep(10)

        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")


    def execute_human_agent(self) -> ExecutionResult:
        """Return structured success / failure; retry until the index sees it."""
        params = {"beneficiary": "Patient/PAT001", "status": "active", "_summary": "false"}

        # ── at most three quick polls: 0.1 s, 0.2 s, 0.4 s
        delay = 0.1
        for attempt in range(5):
            #resp = requests.get(f"{self.FHIR_SERVER_URL}/Coverage", headers=self.HEADERS, params=params)
            resp = requests.get(f"{self.FHIR_SERVER_URL}/Coverage", params=params)

            if resp.status_code != 200:
                return ExecutionResult(
                    False, f"FHIR search failed: {resp.status_code} {resp.text}"
                )

            bundle = resp.json()
            if bundle.get("total", 0) > 0:
                cov_id = bundle["entry"][0]["resource"]["id"] 
                return ExecutionResult(
                    True,
                    f"Found coverage <COVERAGE>{cov_id}</COVERAGE>"
                )

            time.sleep(delay)
            delay *= 2 

        # still nothing after three tries
        return ExecutionResult(
            False,
            "No active coverage found for patient PAT001 after 3 retries"
        )


    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Structured-output assertions
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

    def get_required_tool_call_sets(self) -> list:
        return [
            {"getAllResources": 0},
            {"getResourceById": 0}
        ]

    def get_required_resource_types(self) -> list:
        return ["Coverage"]

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource"]

    def get_difficulty_level(self) -> int:
        return 1

