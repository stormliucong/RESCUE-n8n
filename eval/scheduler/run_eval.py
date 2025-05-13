from dataclasses import asdict
import logging.config
import uuid
from dotenv import load_dotenv # type: ignore
import os
import json
import logging
import yaml
import importlib
import requests

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

load_dotenv()
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
# test FHIR_SERVER_URL 
N8N_AGENT_URL = os.getenv("N8N_AGENT_URL")
N8N_EXECUTION_URL = os.getenv("N8N_EXECUTION_URL")
N8N_SYSTEM_PROMPT_FILE = os.getenv("N8N_SYSTEM_PROMPT_FILE", None)
N8N_MULTI_AGENT_PROMPT_FILE = os.getenv("N8N_MULTI_AGENT_PROMPT_FILE", None)

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
        difficulty_level = task['difficulty_level']
        required_tool_call_sets = task.get('required_tool_call_sets', [])
        required_resource_types = task.get('required_resource_types', [])
        prohibited_tools = task.get('prohibited_tools', [])

        module = importlib.import_module(f"tasks.{module_name}")
        cls = getattr(module, class_name)

        task_configs.append({
            "class": cls,
            "required_tool_call_sets": required_tool_call_sets,
            "required_resource_types": required_resource_types,
            "prohibited_tools": prohibited_tools,
            "difficulty_level": difficulty_level
        })

    return task_configs


def test_fhir_server():
    try:
        response = requests.get(f"{FHIR_SERVER_URL}/metadata", headers=HEADERS)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"FHIR server is not accessible: {str(e)}")
        raise Exception(f"FHIR server is not accessible: {str(e)}")
    return True

def test_n8n():
    try:
        prompt = "Hello, how are you?"
        session_id = str(uuid.uuid4())
        payload = {
            "prompt": prompt,
            "session_id": session_id,
            "fhir_server_url": FHIR_SERVER_URL,
        }
        response = requests.post(N8N_AGENT_URL, json=payload)
        response.raise_for_status()
        try:
            execution_id = response.headers['execution_id']
            response = requests.get(N8N_EXECUTION_URL, params={"executionId": execution_id}, timeout=100)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"N8N execution is not accessible: {str(e)}")
            raise Exception(f"N8N execution is not accessible: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"N8N agent is not accessible: {str(e)}")
        raise Exception(f"N8N agent is not accessible: {str(e)}")
    return True

task_configs = load_tasks_from_config("run_eval_test_2.yaml")

logger.info(f"Running eval with {len(task_configs)} tasks")

agent = "n8n"
logger.info(f"Running eval with agent: {agent}")

if test_fhir_server():
    logger.info("FHIR server is accessible")
if test_n8n():
    logger.info("N8N agent/execution is accessible")


for task_config in task_configs:
    # Initialise task
    task_class = task_config["class"]
    required_tool_call_sets = task_config["required_tool_call_sets"]
    required_resource_types = task_config["required_resource_types"]
    prohibited_tools = task_config["prohibited_tools"]
    difficulty_level = task_config['difficulty_level']

    # Logging extracted values
    logger.info(f"Initialising task: {task_class.__name__}")
    logger.info(f"Required tools sequences: {required_tool_call_sets}")
    logger.info(f"Required resource types: {required_resource_types}")
    logger.info(f"Prohibited tools: {prohibited_tools}")
    logger.info(f"difficulty_level: {difficulty_level}")

    # Defining Task object with evaluation params
    task = task_class(
        fhir_server_url = FHIR_SERVER_URL,
        n8n_url = N8N_AGENT_URL,
        n8n_execution_url = N8N_EXECUTION_URL,
        n8n_system_prompt_file = N8N_SYSTEM_PROMPT_FILE,
        n8n_multi_agent_prompt_file = N8N_MULTI_AGENT_PROMPT_FILE,
        required_tool_call_sets = required_tool_call_sets,
        required_resource_types = required_resource_types,
        prohibited_tools = prohibited_tools
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