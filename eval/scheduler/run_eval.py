from dataclasses import asdict
from dotenv import load_dotenv # type: ignore
from task_01_enter_new_patient import EnterNewPatientTask
from task_17b_reschedule_with_another_provider import RescheduleWithAnotherProviderTask
import os
import json

load_dotenv()
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
N8N_URL = os.getenv("N8N_AGENT_URL")
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

load_dotenv()
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
N8N_URL = os.getenv("N8N_AGENT_URL")
N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")

class_list = [RescheduleWithAnotherProviderTask]
for task_class in class_list:
    print(f"Running task: {task_class.__name__}")

    # Initialise task
    task = task_class(FHIR_SERVER_URL, N8N_URL, N8N_EXECUTION_URL)
    task.cleanup_test_data()
    task.prepare_test_data()

    # Comment when needed
    # print("HUMAN EXECUTION")
    # task_result = task.execute_human_agent()
    print("N8N RESPONSE TASK")
    exec_result = task.execute_n8n_agent()
    #print(exec_result.tool_calls['createResource'])
    #print("EVAL TASK")

    task_result = task.validate_response(exec_result)
    print("TASK RESULT")
    print(task_result.task_success)

    print('RESULT TOOL ORDER')
    print(task_result.execution_result.tool_order)

    # save ExecutionResult object to a json file
    file_name = f"task_{task_result.task_id}_n8n_response.json"
    with open(file_name, "w") as f:
        json.dump(asdict(task_result),f)
        
    print('TASK FAILURE MODE')
    task_failure_mode = task.identify_failure_mode(task_result)

    print('task failure mode: ', task_failure_mode)

    # if task_failure_mode is not None:
    #     file_name = f"task_{task_result.task_id}_failure_mode.json"
    #     with open(file_name, "w") as f:
    #         json.dump(asdict(task_failure_mode),f)