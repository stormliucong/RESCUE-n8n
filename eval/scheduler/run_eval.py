from dataclasses import asdict
import logging.config
import time
import uuid
from dotenv import load_dotenv # type: ignore
import os
import json
import logging
import yaml
import importlib
import requests
import argparse

argparse = argparse.ArgumentParser(description="Run evaluation tasks")
argparse.add_argument(
    "--config",
    type=str,
    default="experiments/experiment.yaml",
    help="Path to the configuration file"
)
argparse.add_argument(
    "--agent",
    type=str,
    default="human",
    choices=["human", "n8n"],
    help="Agent to use for evaluation"
)
argparse.add_argument(
    "--output_dir",
    type=str,
    default="experiments/output",
    help="Directory to save the output files"
)
args = argparse.parse_args()
agent = args.agent
config_path = args.config
output_dir = args.output_dir

# sh command
# python run_eval.py --config experiments/experiment.yaml --agent human --output_dir experiments/output

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

        module = importlib.import_module(f"tasks.{module_name}")
        cls = getattr(module, class_name)

        task_configs.append({
            "class": cls,
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

task_configs = load_tasks_from_config(config_path)
logger.info(f"Running eval with {len(task_configs)} tasks")
logger.info(f"Running eval with agent: {agent}")

if test_fhir_server():
    logger.info("FHIR server is accessible")
if test_n8n():
    logger.info("N8N agent/execution is accessible")


for task_config in task_configs:
   
    # Initialise task
    task_class = task_config["class"]

    # Logging extracted values
    logger.info(f"Initialising task: {task_class.__name__}")

    # Defining Task object with evaluation params
    task = task_class(
        fhir_server_url = FHIR_SERVER_URL,
        n8n_url = N8N_AGENT_URL,
        n8n_execution_url = N8N_EXECUTION_URL,
        n8n_system_prompt_file = N8N_SYSTEM_PROMPT_FILE,
        n8n_multi_agent_prompt_file = N8N_MULTI_AGENT_PROMPT_FILE
    )
    
    task_id = task.get_task_id()
    # save ExecutionResult object to a json file
    file_name = f"task_{task_id}_{agent}_task_result.json"
    file_name = os.path.join(output_dir, file_name)
    os.makedirs(output_dir, exist_ok=True)
    # if file already exists, skip it.
    if os.path.exists(file_name):
        logger.info(f"Task result already exists for task: {task_class.__name__}")
        continue
    
    
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

   
    with open(file_name, "w") as f:
        logger.info(f"Saving task result to {file_name}")
        json.dump(asdict(task_result),f)
        logger.info(f"Saving task result to {file_name}")

    
    if agent == "n8n":
        logger.info(f"Identifying failure mode for task: {task_class.__name__}")
        task_failure_mode = task.identify_failure_mode(task_result) # to be implemented in each tasks.

        if task_failure_mode is not None:
            file_name = f"task_{task_result.task_id}_{agent}_failure_mode.json"
            file_name = os.path.join(output_dir, file_name)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving failure mode to {file_name}")
            with open(file_name, "w") as f:
                logger.info(f"Saving failure mode to {file_name}")
                json.dump(asdict(task_failure_mode),f)
        else:
            logger.info(f"No failure mode identified for task: {task_class.__name__}")
            

# read all *_task_result.json files and summarise the success rate.
task_results = []
for file in os.listdir(output_dir):
    if file.endswith(f"{agent}_task_result.json"):
        file_path = os.path.join(output_dir, file)
        with open(file_path, "r") as f:
            task_result = json.load(f)
            task_results.append(task_result)
            task_success = task_result.get("task_success", False)
            task_id = task_result.get("task_id", None)
            task_name = task_result.get("task_name", None)
            if not task_success:
                logger.warning(f"Task {task_id} ({task_name}) failed")
# calculate success rate
success_count = sum(1 for result in task_results if result.get("task_success", False))
total_count = len(task_results)
# logger failed ones.
for task_result in task_results:
    if not task_result.get("task_success", False):
        logger.warning(f"Task {task_result.get('task_id', None)} ({task_result.get('task_name', None)}) failed")
logger.info(f"Total tasks executed: {total_count}")
logger.info(f"Total tasks succeeded: {success_count}")
logger.info(f"Total tasks failed: {total_count - success_count}")
success_rate = success_count / total_count * 100 if total_count > 0 else 0
logger.info(f"Success rate: {success_rate:.2f}%")