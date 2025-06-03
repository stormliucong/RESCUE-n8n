import os
import importlib.util
import yaml
import argparse
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
import ast

def get_class_names(filepath):
    with open(filepath, "r") as file:
        node = ast.parse(file.read(), filename=filepath)
    return [n.name for n in ast.walk(node) if isinstance(n, ast.ClassDef)]

# Example


def get_task_config(task_file: str, env_file: str) -> Dict[str, Any]:
    # Get module name from file path
    module_name = os.path.splitext(os.path.basename(task_file))[0]
    
    # Find the task class (it should be the only class in the file)
    # without import module
    task_class = get_class_names(task_file)[0]
    
    config = {
        'module': module_name,
        'class': task_class
    }
        
    return config

def generate_task_config(task_dir: str, output_file: str, task_prefix: str = 'task_', env_file: str = None):
    """Generate YAML configuration from task files.
    
    Args:
        task_dir (str): Directory containing task files
        output_file (str): Path to output YAML file
        task_prefix (str): Prefix for task files to process (default: 'task_')
        env_file (str): Path to environment file
    """
    # Find all task_*.py files
    task_files = []
    for file in os.listdir(task_dir):
        if file.startswith(task_prefix) and file.endswith('.py'):
            task_files.append(os.path.join(task_dir, file))
    
    # Sort files to maintain consistent order
    task_files.sort()
    
    # Generate configuration for each task
    tasks = []
    for task_file in task_files:
        try:
            task_config = get_task_config(task_file, env_file)
            tasks.append(task_config)
        except Exception as e:
            print(f"Error processing {task_file}: {str(e)}")
    
    # Write to YAML file
    with open(output_file, 'w') as f:
        yaml.dump({'tasks': tasks}, f, default_flow_style=False, sort_keys=False)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate YAML configuration from task files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--task_dir',
        type=str,
        help='Directory containing task files',
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tasks')
    )
    
    parser.add_argument(
        '--output_yaml',
        type=str,
        help='Path to output YAML file',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiment.yaml')
    )
    
    parser.add_argument(
        '--prefix',
        type=str,
        help='Prefix for task files to process',
        default='task_'
    )
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
        
    generate_task_config(args.task_dir, args.output_yaml, args.prefix)
    print(f"Configuration generated at {args.output_yaml}") 