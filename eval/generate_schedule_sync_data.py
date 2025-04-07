# This is for schedule agent testing purposes.

import requests
import random
import json
from faker import Faker
from tqdm import tqdm
import logging
# from datetime import datetime, timedelta
# import pytz


# Set a global seed
SEED = 0

# Set the seed for random
random.seed(SEED)

# Set the seed for Faker
faker = Faker()


MELD_BUNDLE = "./meld-data/sandbox-export.json"
FHIR_SERVER_URL = "http://165.22.13.117:7070/fhir"
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json"
    }

RESOURCE_TYPES = ["Appointment", "Slot",  "Schedule", "Patient", "Practitioner", "Location"]

def get_resource_ids(resource_type):
    """Fetches all resource IDs for the given resource type."""
    url = f"{FHIR_SERVER_URL}/{resource_type}?_count=100"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Failed to fetch {resource_type}: {response.status_code}")
        return []
    
    data = response.json()
    if "entry" not in data:
        return []
    
    return [entry["resource"]["id"] for entry in data["entry"]]

def delete_resource(resource_type, resource_id):
    """Deletes a specific resource by ID."""
    url = f"{FHIR_SERVER_URL}/{resource_type}/{resource_id}"
    response = requests.delete(url, headers=HEADERS)
    
    if response.status_code in [200, 204]:
        print(f"Deleted {resource_type}/{resource_id}")
    else:
        print(f"Failed to delete {resource_type}/{resource_id}: {response.status_code}")

def delete_all_resources():
    """Deletes all resources of the specified types."""
    for resource_type in RESOURCE_TYPES:
        print(f"Fetching {resource_type} resources...")
        resource_ids = get_resource_ids(resource_type)
        
        if not resource_ids:
            print(f"No {resource_type} resources found.")
            continue
        
        print(f"Deleting {len(resource_ids)} {resource_type} resources...")
        for resource_id in resource_ids:
            delete_resource(resource_type, resource_id)

def load_resources_from_bundle(file_path):
    """
    Reads a FHIR bundle from a file and posts each resource to the FHIR server.
    """
    with open(file_path, "r") as file:
        fhir_bundle = json.load(file)

    if fhir_bundle.get("resourceType") != "Bundle":
        raise ValueError("Invalid FHIR bundle: resourceType is not 'Bundle'")

    url = FHIR_SERVER_URL
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    entries = fhir_bundle.get('entry', [])
    
    priority_order = ["Organization", "Patient"]

    # 排序函数
    def sort_key(entry):
        resource_type = entry['resource']['resourceType']
        if resource_type in priority_order:
            return priority_order.index(resource_type)
        return len(priority_order)

    # 对 entries 进行排序
    entries = sorted(entries, key=sort_key)
    success_count = 0
    error_count = 0
    exist_count = 0
    for entry in tqdm(entries, desc="Processing entries"):
        # 创建一个新的 fhir_bundle，只包含当前的 entry
        single_entry_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [entry]
        }

        resource = entry['resource']
        resource_type = resource['resourceType']
        resource_id = resource['id']
        
        # 检查资源是否已经存在
        check_url = f"{url}/{resource_type}/{resource_id}"
        check_response = requests.get(check_url, headers=headers)
        
        if check_response.status_code in [200, 201]:
            exist_count += 1
            continue
        
        # 打印 single_entry_bundle 以检查其内容
        # print("Single Entry Bundle:", json.dumps(single_entry_bundle, indent=2))
        
        # 将 single_entry_bundle 转换为 JSON 字符串
        single_entry_bundle_str = json.dumps(single_entry_bundle)
        
        response = requests.post(url, data=single_entry_bundle_str, headers=headers)
        if response.status_code in [200, 201]:
            success_count += 1
        else:
            error_count += 1
            print(f"Failed to create {resource_type}/{resource_id}: {response.text}")
    # response = requests.post(url, json=fhir_bundle, headers=headers)
    # if response.status_code in [200, 201]:
    #     return response.json().get("id")
    # else:
    #     print(response.text)
    total_requests = success_count + error_count
    if total_requests > 0:
        error_percentage = (error_count / total_requests) * 100
        print(f"Total Error Percentage: {error_percentage:.2f}% in {total_requests} requests.")
        logging.info(f"Total Error Percentage: {error_percentage:.2f}% in {total_requests} requests.")
    else:
        print("No requests were made.")


def post_to_fhir(resource):
    """
    Posts a FHIR resource to the FHIR server.
    """
    url = f"{FHIR_SERVER_URL}/{resource['resourceType']}"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json"
    }
    response = requests.post(url, json=resource, headers=headers)
    
    if response.status_code in [200, 201]:
        return response.json().get("id")
    else:
        raise ValueError(f"Failed to create {resource['resourceType']}: {response.text}")


def populate_fhir():
    # delete_all_resources()
    load_resources_from_bundle(MELD_BUNDLE)
    

if __name__ == "__main__":
    populate_fhir()