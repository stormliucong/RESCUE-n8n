# task_01_enter_new_patient.py
import os
import requests # type: ignore
import json
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode
from dataclasses import asdict
from dotenv import load_dotenv
import re



class EnterNewPatientTask(TaskInterface):
    def get_task_id(self) -> str:
        return "1"

    def get_task_name(self) -> str:
        return "Enter New Patient"

    def get_prompt(self) -> str:
        return """
                Task: Create a new patient record

                You need to create a new patient with the following information:
                - Full Name: John Doe
                - Birth Date: June 15, 1990
                - Phone Number: (123) 456-7890
                - Address: 123 Main St, Boston, MA

                Return the created patient's ID from the FHIR server using the following format:
                
                    <patient_id>PATIENTID</patient_id>

                """

    def prepare_test_data(self) -> None:
        # Check if FHIR server is accessible
        try:
            response = requests.get(f"{self.FHIR_SERVER_URL}/metadata", headers=self.HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"FHIR server is not accessible: {str(e)}")


    def execute_human_agent(self) -> ExecutionResult:
        payload = {
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": "Doe",
                    "given": ["John"]
                }
            ],
            "birthDate": "1990-06-15",
            "telecom": [
                {
                    "system": "phone",
                    "value": "(123) 456-7890"
                }
            ],
            "address": [
                {
                    "line": ["123 Main St"],
                    "city": "Boston",
                    "state": "MA"
                }
            ]
        }

        response = self.post_to_fhir(payload)
        response_msg = None
        if response.status_code == 201:
            tagged_response = f"<patient_id>{response.json()["id"]}</patient_id>"
                                
            response_msg = f'Patient "John Doe" created successfully with ID: {tagged_response}'
        else:
            response_msg = f'Failed to create patient: {response.status_code} {response.text}'
        
        execution_result = ExecutionResult(
            execution_success=response.status_code == 201,
            response_msg=response_msg,
        )
        return execution_result



    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:

            # Validate the patient resources
            params = {
                "family": "Doe",
                "given": "John"
            }
            response = requests.get(
                f"{self.FHIR_SERVER_URL}/Patient",
                headers=self.HEADERS,
                params=params
            )
            # Check if the patient is created successfully
            assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response body: {response.text}"
            response_json = response.json()
            assert 'entry' in response_json, "No patient found"
            assert len(response_json['entry']) > 0, "No patient found"
            patient = response_json['entry'][0]['resource']
            assert patient['name'][0]['family'] == "Doe", f"Expected family name 'Doe', got {patient['name'][0]['family']}"
            assert patient['name'][0]['given'][0] == "John", f"Expected given name 'John', got {patient['name'][0]['given'][0]}"
            assert patient['birthDate'] == "1990-06-15", f"Expected birth date '1990-06-15', got {patient['birthDate']}"
            
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


            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=True,
                assertion_error_message=None,
            )

        except AssertionError as e:
            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=str(e),
            )
        except Exception as e:
            return TaskResult(
                task_id = self.get_task_id(),
                task_name = self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=f"Unexpected error: {str(e)}",
            )
            
