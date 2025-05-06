# task_02a_search_existing_patient.py

import os
import requests
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode

class SearchExistingPatientTask(TaskInterface):
    def get_task_id(self) -> str:
        return "2a"

    def get_task_name(self) -> str:
        return "Search Existing Patient"

    def get_prompt(self) -> str:
        return """
                Task: Search for an existing patient

                Search the database for the following patient:
                - Full Name: John Doe
                - Birth Date: June 15, 1990

                If the patient exists, return their Patient resource ID.
                If the patient doesn't exist, classify them as a new patient.

                Return the searched patient's ID from the FHIR server using the following format:
                
                    <patient_id>PATIENTID</patient_id>
                """

    def prepare_test_data(self) -> None:
        try:
            # Clean up existing resources
            self.delete_all_resources()

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


    def execute_human_agent(self) -> ExecutionResult:
        search_params = {
            "family": "Doe",
            "given": "John",
            "birthdate": "1990-06-15"
        }
        
        response = requests.get(
            f"{self.FHIR_SERVER_URL}/Patient",
            headers=self.HEADERS,
            params=search_params
        )
        
        if response.status_code != 200:
            return ExecutionResult(
                execution_success=False,
                response_msg=f"Failed to search for patient: {response.text}"
            )

        response_json = response.json()
        tagged_response = f"<patient_id>{response_json['entry'][0]['resource']['id']}</patient_id>"

        return ExecutionResult(
            execution_success=True,
            response_msg=f"Found patient with ID {tagged_response}"
        )



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            # Verify the patient was found correctly
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Patient",
                headers=self.HEADERS,
                params={
                    "family": "Doe",
                    "given": "John",
                    "birthdate": "1990-06-15"
                }
            )
            
            assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
            
            response_json = response.json()
            assert 'total' in response_json, "Expected to find total in the response"
            assert response_json['total'] > 0, "Expected to find at least one patient"
            assert 'entry' in response_json, "Expected to find entry in the response"
            assert len(response_json['entry']) > 0, "Expected to find at least one patient"

            # Validate the patient details
            patient = response_json['entry'][0]['resource']
            assert patient['resourceType'] == "Patient", "Resource type must be Patient"
            assert patient['name'][0]['family'] == "Doe", "Invalid family name"
            assert patient['name'][0]['given'][0] == "John", "Invalid given name"
            assert patient['birthDate'] == "1990-06-15", "Invalid birth date"

            # Check if returned result matches the human executed request's return.
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            
                # Parse the response message
            response_msg = response_msg.strip()
                # match the response message with the expected format
            assert "<patient_id>" in response_msg, "Expected to find <patient_id> tag"
            assert "</patient_id>" in response_msg, "Expected to find </patient_id>tag"
            
                # Extract the patient_id from the response message
            patient_id = response_msg.split("<patient_id>")[1].split("</patient_id>")[0]
            assert patient_id is not None, "Expected to find patient_id"
            
                # slot id should be 
            expected_patient_id = self.execute_human_agent().response_msg.split("<patient_id>")[1].split("</patient_id>")[0]
            assert patient_id == expected_patient_id, f"Expected patient_id {expected_patient_id}, got {patient_id}"


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

