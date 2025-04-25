from dotenv import load_dotenv # type: ignore
from task_01_enter_new_patient import EnterNewPatientTask
import os
load_dotenv()
FHIR_SERVER_URL = os.getenv("FHIR_SERVER_URL")
N8N_URL = os.getenv("N8N_AGENT_URL")
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
}

class_list = [EnterNewPatientTask]
for task_class in class_list:
    task = task_class(FHIR_SERVER_URL, N8N_URL)
    task.cleanup_test_data()
    task.prepare_test_data()
    # human_response = task.execute_human_agent()
    # eval_results = task.validate_response(human_response)
    # print(eval_results)
    n8n_response = task.execute_n8n_agent()
    print(n8n_response)