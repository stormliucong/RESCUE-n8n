from dataclasses import asdict
import logging.config
from dotenv import load_dotenv # type: ignore
import os
import json
import logging
import yaml
import importlib

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


def load_tasks_from_config(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    task_configs = []
    for task in config.get('tasks', []):
        module_name = task['module']
        class_name = task['class']
        required_tool_call_sets = task.get('required_tool_call_sets', [])
        required_resource_types = task.get('required_resource_types', [])

        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)

        task_configs.append({
            "class": cls,
            "required_tool_call_sets": required_tool_call_sets,
            "required_resource_types": required_resource_types
        })

    return task_configs



task_configs = load_tasks_from_config("run_eval_test.yaml")
# task_configs = load_tasks_from_config("run_eval_with_params.yaml")


logger.info(f"Running eval with {len(task_configs)} tasks")

agent = "n8n"
logger.info(f"Running eval with agent: {agent}")

# sample 2 items from task_configs

for task_config in task_configs:
    # Initialise task
    task_class = task_config["class"]
    required_tool_call_sets = task_config["required_tool_call_sets"]
    required_resource_types = task_config["required_resource_types"]

    # Logging extracted values
    logger.info(f"Initialising task: {task_class.__name__}")
    logger.info(f"Required tools sequences: {required_tool_call_sets}")
    logger.info(f"Required resource types: {required_resource_types}")

    # Defining Task object with evaluation params
    task = task_class(
        FHIR_SERVER_URL,
        N8N_URL,
        N8N_EXECUTION_URL,
        required_tool_call_sets=required_tool_call_sets,
        required_resource_types=required_resource_types
    )

    logger.info(f"Cleaning up test data for task: {task_class.__name__}")
    task.cleanup_test_data()

    logger.info(f"Preparing test data for task: {task_class.__name__}")
    task.prepare_test_data()

    # Comment when needed
    if agent == "human":
        logger.info(f"Executing task on human agent: {task_class.__name__}")
        exec_result = task.execute_human_agent()
        logger.debug(f"Human response:")
        logger.debug(exec_result)
    if agent == "n8n":
        logger.info(f"Executing task on N8N: {task_class.__name__}")
        exec_result = task.execute_n8n_agent()
        logger.debug(f"N8N response:")
        logger.debug(exec_result)
    
    logger.info(f"Validating response for task: {task_class.__name__}")
    task_result = task.validate_response(exec_result)
    logger.debug(f"Task result:")

    # save ExecutionResult object to a json file
    file_name = f"task_{task_result.task_id}_{agent}_task_result.json"
    with open(file_name, "w") as f:
        logger.info(f"Saving task result to {file_name}")
        json.dump(asdict(task_result),f)
    
    if agent == "n8n":
        logger.info(f"Identifying failure mode for task: {task_class.__name__}")
        task_failure_mode = task.identify_failure_mode(task_result)

    if task_failure_mode is not None:
        file_name = f"task_{task_result.task_id}_{agent}_failure_mode.json"
        with open(file_name, "w") as f:
            logger.info(f"Saving failure mode to {file_name}")
            json.dump(asdict(task_failure_mode),f)
    else:
        logger.info(f"No failure mode identified for task: {task_class.__name__}")