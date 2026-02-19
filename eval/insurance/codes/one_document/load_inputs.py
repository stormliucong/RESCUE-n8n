import json

def load_inputs(case_path, ground_truth_path):
    '''Load case examples and ground-truth JSON files'''
    with open(case_path, "r") as f:
        case = json.load(f)

    with open(ground_truth_path, "r") as f:
        ground_truth = json.load(f)

    return case, ground_truth