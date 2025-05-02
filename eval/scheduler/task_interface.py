from abc import ABC, abstractmethod
import time
from typing import Dict, Any, List, Optional, Tuple 
import requests # type: ignore
from dataclasses import dataclass
from fetch_and_parse_n8n_execution_log import fetch_and_parse_n8n_execution_log
import json
import logging

logging.basicConfig(level=logging.INFO, filename='task_interface.log', filemode='w')


@dataclass
class ExecutionResult:
    execution_success: bool = False
    response_msg: Optional[str] = None
    execution_id: Optional[str] = None
    workflow_name: Optional[str] = None
    #raw_log: Optional[Dict[str, Any]] = None
    token_total: Optional[int] = None
    input_query: Optional[str] = None
    total_exec_ms: Optional[float] = None
    tool_order: Optional[list[str]] = None
    tool_exec_ms: Optional[Dict[str, float]] = None
    tool_calls: Optional[Dict[str, list[Dict[str, Any]]]] = None
    tool_call_counts: Optional[Dict[str, int]] = None
    


@dataclass
class TaskResult:
    task_success: bool = False
    assertion_error_message: Optional[str] = None
    task_id: Optional[str] = None
    task_name: Optional[str] = None
    execution_result: Optional[ExecutionResult] = None
    


@dataclass
class TaskFailureMode:
    incorrect_tool_selection: Optional[bool] = False
    incorrect_tool_order: Optional[bool] = False
    incorrect_resource_type: Optional[bool] = False
    error_codes: Optional[List[str]] = None # https://build.fhir.org/codesystem-assert-response-code-types.html



class TaskInterface(ABC):
    def __init__(self, fhir_server_url, n8n_url, n8n_execution_url):

        self.FHIR_SERVER_URL = fhir_server_url
        self.N8N_AGENT_URL = n8n_url
        self.N8N_EXECUTION_URL = n8n_execution_url
        
        print(f"FHIR_SERVER_URL: {self.FHIR_SERVER_URL}")
        print(f"N8N_AGENT_URL: {self.N8N_AGENT_URL}")
        print(f"N8N_EXECUTION_URL: {self.N8N_EXECUTION_URL}")
        
        
        self.HEADERS = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json"
        }
        self.RESOURCE_TYPES = [
            "Patient",
            "Condition",
            "Procedure",
            "Coverage",
            "Practitioner",
            "Organization",
            "RelatedPerson",
            "Consent",
            "DocumentReference",
            "Slot",
            "Schedule",
            "Appointment",
        ]
        
    def get_resource_ids(self, resource_type):
        """Fetches all resource IDs for the given resource type, handling pagination."""
        url = f"{self.FHIR_SERVER_URL}/{resource_type}?_count=1000"
        resource_ids = []
        while url:
            response = requests.get(url, headers=self.HEADERS)
            if response.status_code != 200:
                print(f"Failed to fetch {resource_type}: {response.status_code}")
                break
            
            data = response.json()
            if "entry" in data:
                resource_ids.extend([entry["resource"]["id"] for entry in data["entry"]])

            # Find the next page URL
            next_url = None
            if "link" in data:
                for link in data["link"]:
                    if link["relation"] == "next":
                        next_url = link["url"]
                        break

            url = next_url  # continue if next page exists, else break the loop
        return resource_ids
        

    def delete_resource(self, resource_type, resource_id):
        """Deletes a specific resource by ID, removing any references to it first.
        recursively delete all resources that reference the resource_id
        """
        # Find any resources that reference this one
        url = f"{self.FHIR_SERVER_URL}/{resource_type}/{resource_id}"
        rev_url = f"{self.FHIR_SERVER_URL}/{resource_type}?_id={resource_id}&_revinclude:iterate=*"
        response = requests.get(rev_url, headers=self.HEADERS)
        if response.status_code != 200:
            print(response.json())
            print(f"Failed to revinclude for {url}")
            return
        bundle = response.json()
        entries = bundle.get("entry", [])
        for entry in entries:
            child = entry["resource"]
            child_type = child["resourceType"]
            child_id = child["id"]
            if f"{child_type}/{child_id}" != f"{resource_type}/{resource_id}":  # avoid self-reference
                self.delete_resource(child_type, child_id)
        
        # Now delete the resource itself
        # print(f"Deleting {url}...")
        del_response = requests.delete(url, headers=self.HEADERS)
        # print(f"DELETE {url}: {del_response.status_code}")
        time.sleep(0.1)  # avoid overwhelming the server
        
        
    def delete_all_resources(self):
        """Deletes all resources of the specified types in the correct order to handle dependencies."""
        # Define the order of deletion based on dependencies
        # Resources that depend on others should be deleted first
        # Not necessary b/c delete_resource handles dependencies
        # But it is more efficient to delete in this order.
        deletion_order = [
            "Appointment",      # Depends on Patient, Practitioner, Location, Slot
            "Slot",            # Depends on Schedule
            "Schedule",        # Depends on Practitioner
            "DocumentReference", # Depends on Patient, Practitioner
            "Consent",         # Depends on Patient, Organization, DocumentReference
            "Account",         # Depends on Patient, RelatedPerson
            "RelatedPerson",   # Depends on Patient
            "Coverage",        # Depends on Patient, Organization
            "Procedure",       # Depends on Patient
            "Condition",       # Depends on Patient
            "ServiceRequest",  # Depends on Patient
            "CarePlan",        # Depends on Patient, Encounter
            "Location",        # No dependencies
            "Organization",    # No dependencies
            "Patient",         # No dependencies
            "Practitioner",    # No dependencies
        ]

        for resource_type in deletion_order:
            # print(f"\nProcessing {resource_type} resources...")
            resource_ids = self.get_resource_ids(resource_type)

            if not resource_ids:
                # print(f"No {resource_type} resources found.")
                continue

            # print(f"Deleting {len(resource_ids)} {resource_type} resources...")
            for resource_id in resource_ids:
                self.delete_resource(resource_type, resource_id)
                # Add a small delay to prevent overwhelming the server
                time.sleep(0.1)
    

    def post_to_fhir(self,resource):
        """
        Posts a FHIR resource to the FHIR server.
        """
        url = f"{self.FHIR_SERVER_URL}/{resource['resourceType']}"
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }
        response = requests.post(url, json=resource, headers=headers)

        if response.status_code in [200, 201]:
            return response
        else:
            raise ValueError(
                f"Failed to create {resource['resourceType']}: {response.text}"
            )
            

    def upsert_to_fhir(self,resource):
        """
        Creates or updates a FHIR resource on the FHIR server with a specified ID.
        """
        url = f"{self.FHIR_SERVER_URL}/{resource['resourceType']}/{resource['id']}"
        headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }
        response = requests.put(url, json=resource, headers=headers)

        if response.status_code in [200, 201]:
            # print(
            #     f"Successfully upserted {resource['resourceType']} with ID {resource['id']}"
            # )
            return None
        else:
            print(
                f"Failed to upsert {resource['resourceType']} with ID {resource['id']}: {response.status_code} {response.text}"
            )
            return response
            

    @abstractmethod
    def get_task_id(self) -> str:
        """Return the task ID"""
        pass


    @abstractmethod
    def get_task_name(self) -> str:
        """Return the task name"""
        pass


    @abstractmethod
    def get_prompt(self) -> str:
        """Return the prompt for the task"""
        pass


    @abstractmethod
    def prepare_test_data(self) -> None:
        """Prepare any necessary FHIR resources for the test"""
        pass


    def cleanup_test_data(self) -> None:
        """Clean up any test data created during the test"""
        self.delete_all_resources()
        

    def execute_n8n_agent(self) -> ExecutionResult:
        """Execute the task on n8n workflowand and return results"""
        prompt = self.get_prompt()
        print(prompt)
        payload = {
            "prompt": prompt,
            "fhir_server_url": self.FHIR_SERVER_URL
        }
        try:
            response = requests.post(self.N8N_AGENT_URL, json=payload)
    
            if response.status_code == 200:
                success = True
                response_msg = response.json()[0]['output']
                # get response header
                execution_id = response.headers['execution_id'] 
            else:
                success = False
                response_msg = f"Error: {response.status_code} - {response.text}"
                execution_id = response.headers['execution_id'] if 'execution_id' in response.headers else None
        except Exception as e:
            success = False
            response_msg = f"Unexpected error: {str(e)}"
            execution_id = None 
            
        execution_result = ExecutionResult(
            execution_success=success,
            response_msg=response_msg,
            execution_id=execution_id
        )

        execution_result = self.get_details_by_execution_id(execution_result)

        return execution_result
            
    

    @abstractmethod
    def execute_human_agent(self) -> ExecutionResult:
        """Execute the expected actions that a human should perform"""
        pass
    


    def get_details_by_execution_id(self, execution_result: ExecutionResult) -> ExecutionResult:
        """Get the details of the execution by ID"""
        try:
            execution_id = execution_result.execution_id
            if execution_id is None:
                raise ValueError("Execution ID is None")
            # Fetch and parse the execution log

            result = fetch_and_parse_n8n_execution_log(
                execution_id=execution_id,
                webhook_url=self.N8N_EXECUTION_URL
            )
            #print(result)

            
        except Exception as e:
            print(f"Error fetching execution log: {e}")
            result = {
                "workflow_name": None,
                #"raw_log": None,
                "final_out": None,
                "token_total": None,
                "input_query": None,
                "total_exec_ms": None,
                "tool_exec_ms": None,
                "tool_order": None,
                "tool_calls": None,
                "tool_call_counts": None,
            }

        return ExecutionResult(
            execution_success=execution_result.execution_success,
            response_msg=execution_result.response_msg,
            execution_id=execution_result.execution_id,
            workflow_name=result["workflow_name"],
            #raw_log=result["raw_log"],
            token_total=result["token_total"],
            input_query=result["input_query"],
            total_exec_ms=result["total_exec_ms"],
            tool_exec_ms=result["tool_exec_ms"],
            tool_order=result["tool_order"],
            tool_calls = result["tool_calls"],
            tool_call_counts=result["tool_call_counts"]
        )
        


    def get_json_from_response_msg(self, response_msg: str) -> Optional[Dict[str, Any]]:
        """Parse the JSON part in the string"""
        try:
            # Find the first occurrence of '{' and the last occurrence of '}'
            start = response_msg.index('{')
            end = response_msg.rindex('}') + 1
            json_str = response_msg[start:end]
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            print("Failed to parse JSON from response message.")
            return None
        except Exception as e:
            print(f"Unexpected error while parsing JSON: {str(e)}")
            return None
    
    def check_tool_calls(self, task_result: TaskResult, required_tool_calls: List[List[str]], required_tool_orders: List[List[str]], required_resource_types: List[str]) -> TaskFailureMode:
        """Check the tool calls and return the result"""
        if task_result.task_success:
            return None
        else:
            execution_result = task_result.execution_result
            if execution_result is None:
                return None
            
            incorrect_tool_selection = True
            incorrect_tool_order = True
            incorrect_resource_type = True
            error_codes = None
            
            if execution_result.tool_calls is not None:
                for required_tool_call in required_tool_calls:
                    # OR condition
                    i = 0
                    for required_tool_call_x in required_tool_call:
                        # AND condition
                        if required_tool_call_x in execution_result.tool_calls:
                            i += 1
                        if i == len(required_tool_call):
                            incorrect_tool_selection = False

                if incorrect_tool_selection == False:
                    # AND condition
                    i = 0
                    for required_tool_order in required_tool_orders:
                        first_required_tool_list= execution_result.tool_calls[required_tool_order[0]]
                        second_required_tool_list = execution_result.tool_calls[required_tool_order[1]]
                        # order by 'startTime' a loose criteria
                        first_required_tool_first_start = sorted(first_required_tool_list, key=lambda x: x['startTime'])[0]
                        second_required_tool_last_start = sorted(second_required_tool_list, key=lambda x: x['startTime'],reverse=True)[0]
                        if second_required_tool_last_start['startTime'] > first_required_tool_first_start['startTime']:
                            i += 1
                    if i == len(required_tool_orders):
                        incorrect_tool_order = False
                    
                    # collect all resource types from the tool calls
                    error_codes, resource_types = self.get_error_codes(execution_result)
                    if "Slot" in resource_types and "Appointment" in resource_types:
                        incorrect_resource_type = False
            
            return TaskFailureMode(
                incorrect_tool_selection=incorrect_tool_selection,
                incorrect_tool_order=incorrect_tool_order,
                incorrect_resource_type=incorrect_resource_type,
                error_codes=error_codes
            )
    
    def get_error_codes(self, executionResult: ExecutionResult) -> List[str]:
        """Get the error codes from the execution result"""
        error_codes = []
        resource_types = []
        tools = ['createResource', 'updateResource', 'deleteResource', 'getAllResources', 'getResource']
        try:
            # loop through all tool calls
            for tool in executionResult.tool_calls.keys():
                if tool in tools:
                    resource_types.append(executionResult.tool_calls[tool][-1]["input"]['resourceType'])
                    output = executionResult.tool_calls[tool][-1]['output']
                    # Check whether the output is a json object
                    if isinstance(output, str):
                        try:
                            json.loads(output)
                        except json.JSONDecodeError:
                            error_codes.append(output)
        except KeyError as e:
            print(f"KeyError: {str(e)}")
        return error_codes, resource_types
       
            
    
    
    @abstractmethod
    def validate_response(self, executionResult: ExecutionResult) -> TaskResult:
        """Validate the response using assertions"""
        pass
    

    
    @abstractmethod
    def identify_failure_mode(self, executionResult: ExecutionResult) -> TaskFailureMode:
        """Identify the failure mode of the execution"""
        pass

