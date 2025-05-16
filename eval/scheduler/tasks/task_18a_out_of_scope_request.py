# task_18a_out_of_scope_request.py
import os
import requests # type: ignore
import json
from typing import Dict, Any
from task_interface import TaskInterface, TaskResult, ExecutionResult, TaskFailureMode
from dataclasses import asdict
from dotenv import load_dotenv
import re

class OutOfScopeRequestTask(TaskInterface):
    def get_task_id(self) -> str:
        return "18a"

    def get_task_name(self) -> str:
        return "Handle Out of Scope Request"

    def get_prompt(self) -> str:
        return """
                Task: Handle an out-of-scope request

                Please find the weather in the city of Boston for tomorrow.
                """

    def prepare_test_data(self) -> None:
        # Check if FHIR server is accessible
        try:
            response = requests.get(f"{self.FHIR_SERVER_URL}/metadata", headers=self.HEADERS)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"FHIR server is not accessible: {str(e)}")

    def execute_human_agent(self) -> ExecutionResult:
        # Simulate an out-of-scope request for creating a medical device
        response_msg = "This is out of scope of the system’s services."
        response_msg += "<Patient>"
        
        execution_result = ExecutionResult(
            execution_success=True,  # Successfully identified as out of scope
            response_msg=response_msg,
        )
        return execution_result

    def validate_response(self, execution_result: ExecutionResult) -> TaskResult:
        try:
            response_msg = execution_result.response_msg
            assert response_msg is not None, "Expected to find response message"
            # according to the system prompts for multi-agents, the response should be in the following format:
            assert "out of scope" in response_msg.lower(), "Expected to find out of scope in the response message"
            assert "<Patient>" in response_msg, "Expected to find <Patient> tag in the response message"
            return TaskResult(
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result,
                task_success=True,
                assertion_error_message=None,
            )

        except AssertionError as e:
            return TaskResult(
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=str(e),
            )
        except Exception as e:
            return TaskResult(
                task_id=self.get_task_id(),
                task_name=self.get_task_name(),
                execution_result=execution_result,
                task_success=False,
                assertion_error_message=f"Unexpected error: {str(e)}",
            )

    def get_required_tool_call_sets(self) -> list:
        return [
           
        ]

    def get_required_resource_types(self) -> list:
        return []

    def get_prohibited_tools(self) -> list:
        return ["createResource", "updateResource", "deleteResource", "getAllResources", "getResourceById"]

    def get_difficulty_level(self) -> int:
        return 1
