from abc import ABC, abstractmethod
import time
from typing import Dict, Any, List, Optional, Tuple 
import requests # type: ignore
from dataclasses import dataclass
from fetch_and_parse_n8n_execution_log import fetch_and_parse_n8n_execution_log
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
    incorrect_tool_selection: Optional[bool] = None
    incorrect_tool_order: Optional[bool] = None
    incorrect_resource_type: Optional[bool] = None
    prohibited_tool_used: Optional[bool] = None
    error_codes: Optional[List[str]] = None # https://build.fhir.org/codesystem-assert-response-code-types.html



class TaskInterface(ABC):
    def __init__(self,
                fhir_server_url,
                n8n_url,
                n8n_execution_url,
                n8n_system_prompt_file=None,
                required_tool_call_sets=None,
                required_resource_types=None,
                prohibited_tools=None,
                difficulty_level = None):

        self.FHIR_SERVER_URL = fhir_server_url
        self.N8N_AGENT_URL = n8n_url
        self.N8N_EXECUTION_URL = n8n_execution_url

        # Eval parameters
        self.required_tool_call_sets = required_tool_call_sets or []
        self.required_resource_types = required_resource_types or []
        self.prohibited_tools = prohibited_tools or []
        self.difficulty_level = difficulty_level
        self.N8N_SYSTEM_PROMPT_FILE = n8n_system_prompt_file
        print(f"INIT: {required_tool_call_sets=}, {required_resource_types=}")

        
        
        logger.debug(f"FHIR_SERVER_URL: {self.FHIR_SERVER_URL}")
        logger.debug(f"N8N_AGENT_URL: {self.N8N_AGENT_URL}")
        logger.debug(f"N8N_EXECUTION_URL: {self.N8N_EXECUTION_URL}")
        logger.debug(f"N8N_SYSTEM_PROMPT_FILE: {self.N8N_SYSTEM_PROMPT_FILE}")
        
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
                logger.error(f"Failed to fetch {resource_type}: {response.status_code}")
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
            logger.error(f"Failed to revinclude for {url}")
            logger.error(response.json())
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
        del_response = requests.delete(url, headers=self.HEADERS)
        logger.debug(f"DELETE {url}: {del_response.status_code}")
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
            logger.debug(f"\nProcessing {resource_type} resources...")
            resource_ids = self.get_resource_ids(resource_type)

            if not resource_ids:
                logger.debug(f"No {resource_type} resources found.")
                continue

            logger.debug(f"Deleting {len(resource_ids)} {resource_type} resources...")
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
            logger.debug(
                f"Successfully upserted {resource['resourceType']} with ID {resource['id']}"
            )
            return None
        else:
            logger.error(
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
        logger.debug(prompt)
        if self.N8N_SYSTEM_PROMPT_FILE:
            # load txt file into string
            with open(self.N8N_SYSTEM_PROMPT_FILE, 'r') as file:
                system_prompt = file.read()
            logger.debug(f"system_prompt: {system_prompt}")
            # add a reminder with the current date and time
            system_prompt += f'''
                            \n\n## Final Reminder: 
                            The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            Remember the FHIR server stores timestamps in UTC by default, 
                            You have to convert the time zone difference when creating and retrieve resources.
            '''
            payload = {
                "prompt": prompt,
                "fhir_server_url": self.FHIR_SERVER_URL,
                "system_prompt": system_prompt
            }
        else:
            payload = {
                "prompt": prompt,
                "fhir_server_url": self.FHIR_SERVER_URL,
            }
        try:

            #response = requests.post(self.N8N_AGENT_URL, json=payload)

            # TESTING
            print("calling python server")
            SCHEDULER_PROXY_URL = "http://localhost:8000/eval/scheduler"
            response = requests.post(SCHEDULER_PROXY_URL, json=payload)

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
            logger.error(f"Error fetching execution log: {e}")
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
            logger.error("Failed to parse JSON from response message.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while parsing JSON: {str(e)}")
            return None
    



    def check_tool_calls(
        self,
        task_result: TaskResult,
        required_tool_call_sets: List[Dict[str, Optional[int]]],
        required_resource_types: List[str],
        prohibited_tools: Optional[List[str]] = None,
        ) -> TaskFailureMode | None:
        """
        Failure analysis with tri‑state flags
        ------------------------------------
        False → check performed & passed | True → check performed & failed | None → not evaluated

        Flags returned in `TaskFailureMode`
        -----------------------------------
        • prohibited_tool_used     – any disallowed tool called  
        • incorrect_tool_selection – missing required tool(s)  
        • incorrect_tool_order     – required tools out of order  
        • incorrect_resource_type  – wrong resource types  
        • error_codes              – list captured from execution

        Steps
        -----
        1.  Iterate `required_tool_call_sets` until a template’s selection & order both pass.  
        2.  If (1) passes, verify resource types & capture error codes.  
        3.  Independently flag `prohibited_tool_used` without altering other flags.  
        4.  Return `None` on overall task success; otherwise a populated `TaskFailureMode`.
        Given a TaskResult (which wraps an ExecutionResult) decide *why* a task failed.

        Each element in `required_tool_call_sets` is a **template** for one legal tool‑usage
        pattern.  
        • Key  – tool name  
        • Value – required position index (0, 1, 2, …) **or** None if order is irrelevant.

        The logic tries every template in the list until one matches:

            1.  Every tool mentioned in the template must appear in `execution_result.tool_order`
                → otherwise `incorrect_tool_selection` stays True and we try the next template.

            2.  If the template has *ordered* tools (values that are integers) they must appear
                as a subsequence in `tool_order` in the given order.  
                Example: required order `["A","B","C"]` is satisfied by  
                `"B A D B A C F"` because `A … B … C` exists.

            3.  Only after (1) **and** (2) succeed do we check resource types and error codes.
        """
        # --- Fast exit ------------------------------------------------------------------
        if task_result.task_success or task_result.execution_result is None:
            return None

        exec_res: ExecutionResult = task_result.execution_result
        tool_order: List[str] = exec_res.tool_order or []

        # --- Initialise flags -----------------------------------------------------------
        prohibited_tool_used      : Optional[bool] = None
        incorrect_tool_selection  : Optional[bool] = None
        incorrect_tool_order      : Optional[bool] = None
        incorrect_resource_type   : Optional[bool] = None
        error_codes = None

        # --- 1) Match templates ---------------------------------------------------------
        for template in required_tool_call_sets:
            logger.debug(f"analysing template → {template}")

            # -------- selection check --------
            if not all(t in tool_order for t in template):
                logger.debug("missing required tools, trying next template")
                continue
            incorrect_tool_selection = False
            logger.debug("all required tools present")

            # -------- order check --------
            ordered = [(t, idx) for t, idx in template.items() if isinstance(idx, int)]
            ordered.sort(key=lambda x: x[1])
            ordered_names = [t for t, _ in ordered]

            if not ordered_names:
                incorrect_tool_order = False
                logger.debug("template has no order constraints — automatically OK")
            else:
                want = 0
                for t in tool_order:
                    if t == ordered_names[want]:
                        want += 1
                        if want == len(ordered_names):
                            incorrect_tool_order = False
                            logger.debug(f"order satisfied → {ordered_names}")
                            break
                if incorrect_tool_order is None:
                    incorrect_tool_order = True
                    logger.debug(f"order NOT satisfied → {ordered_names}")

            # stop when both checks passed
            if incorrect_tool_selection is False and incorrect_tool_order is False:
                break

        # if no template matched at all
        if incorrect_tool_selection is None:
            incorrect_tool_selection = True
            logger.debug("no template matched — selection failed")

        # --- 2) Resource/type & error codes --------------------------------------------
        if incorrect_tool_selection is False:
            error_codes, res_types = self.get_error_codes(exec_res)
            incorrect_resource_type = not all(rt in res_types for rt in required_resource_types)
            logger.debug(f"resource types seen → {res_types}")
            logger.debug(f"error codes captured → {error_codes}")

        # --- 3) Prohibited‑tool scan ----------------------------------------------------
        if prohibited_tools is not None:
            prohibited_tool_used = False
            for bad in prohibited_tools:
                if bad in tool_order:
                    prohibited_tool_used = True
                    logger.debug(f"prohibited tool used → {bad}")
                    break

        # --- 4) Return structured result -----------------------------------------------
        return TaskFailureMode(
            prohibited_tool_used     = prohibited_tool_used,
            incorrect_tool_selection = incorrect_tool_selection,
            incorrect_tool_order     = incorrect_tool_order,
            incorrect_resource_type  = incorrect_resource_type,
            error_codes              = error_codes,
        )
    

    # Add return type hint
    def get_error_codes(self, executionResult: ExecutionResult):
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
            logger.error(f"KeyError: {str(e)}")
        return error_codes, resource_types
       
            
    
    
    @abstractmethod
    def validate_response(self, executionResult: ExecutionResult) -> TaskResult:
        """Validate the response using assertions"""
        pass
    

    
    def identify_failure_mode(self, task_result: TaskResult) -> TaskFailureMode:
        """
        Default implementation using metadata from YAML.
        Override if task-specific logic is needed.
        """
        if not self.required_tool_call_sets and not self.required_resource_types:
            return TaskFailureMode()  # Nothing to check against

        failure_mode = self.check_tool_calls(
            task_result,
            self.required_tool_call_sets,
            self.required_resource_types,
            self.prohibited_tools
        )

        # if failure_mode is None:
        #     failure_mode = TaskFailureMode(
        #         incorrect_tool_selection=False,
        #         incorrect_tool_order=False,
        #         incorrect_resource_type=False,
        #         error_codes=None
        #     )

        return failure_mode
    
    

    def get_difficulty_level(self):
        # Return the difficulty level
        return self.difficulty_level



