from dataclasses import asdict
import logging.config
from dotenv import load_dotenv # type: ignore
from task_01_enter_new_patient import EnterNewPatientTask
from task_17b_reschedule_with_another_provider import RescheduleWithAnotherProviderTask
import os
import json
import logging

logging.config.fileConfig('logging.ini')
logger = logging.getLogger(__name__)

load_dotenv()
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
N8N_URL = os.getenv("N8N_AGENT_URL")
N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

class_list = [RescheduleWithAnotherProviderTask]
for task_class in class_list:

    # Initialise task
    logger.info(f"Initialising task: {task_class.__name__}")
    task = task_class(FHIR_SERVER_URL, N8N_URL, N8N_EXECUTION_URL)

    logger.info(f"Cleaning up test data for task: {task_class.__name__}")
    task.cleanup_test_data()

    logger.info(f"Preparing test data for task: {task_class.__name__}")
    task.prepare_test_data()

    # Comment when needed
    # logger.info(f"Executing task on human agent: {task_class.__name__}")
    # exec_result = task.execute_human_agent()
    
    logger.info(f"Executing task on N8N: {task_class.__name__}")
    exec_result = task.execute_n8n_agent()
    logger.debug(f"N8N response:")
    logger.debug(exec_result.tool_calls['createResource'])
    #logger.info("EVAL TASK")

    task_result = task.validate_response(exec_result)
    logger.debug("N8N TASK RESULT")
    logger.debug(task_result.task_success)

    logger.debug('RESULT TOOL ORDER')
    logger.debug(task_result.execution_result.tool_order)

    # save ExecutionResult object to a json file
    file_name = f"task_{task_result.task_id}_n8n_response.json"
    with open(file_name, "w") as f:
        logger.info(f"Saving N8N task result to {file_name}")
        json.dump(asdict(task_result),f)
        
    logger.info(f"Identifying failure mode for task: {task_class.__name__}")
    task_failure_mode = task.identify_failure_mode(task_result)

    if task_failure_mode is not None:
        file_name = f"task_{task_result.task_id}_failure_mode.json"
        with open(file_name, "w") as f:
            logger.info(f"Saving failure mode to {file_name}")
            json.dump(asdict(task_failure_mode),f)
    else:
        logger.info(f"No failure mode identified for task: {task_class.__name__}")
