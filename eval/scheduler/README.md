# Scheduler Module Evaluation

This module provides functionality for managing medical appointments and scheduling in a genetic healthcare system. It will evaluate a comprehensive scheduling agent that handles patient appointments, waitlists, and provider availability with interaction with a FHIR server or internal triage workflow

## Overview

The scheduler module is built on top of FHIR (Fast Healthcare Interoperability Resources) standards and provides the following key functionalities:

- Patient management and verification
- Appointment scheduling and cancellation
- Waitlist management
- Provider availability tracking
- Medical history and insurance information management
- Guarantor management

## Components

### Start FHIR 
- `restart_fhir.sh`: start FHIR server for evaluation
- `docker-composer.yaml`: Docker container to start a fhir server


### Scheduler Evaluation Class

   `[1-17]_*.py`: implement various healthcare scheduling and patient management scenarios. Each class is designed to work with a FHIR server and includes proper error handling and verification of results. Each class implement `task_interface.py`

## Setup

1. Ensure you have the required environment variables set in `.env`; Check `env.example` for details
   - `FHIR_SERVER_URL`: The URL of your FHIR server; If you don't have a FHIR server, you can spin up a local one using `restart_fhir.sh`; Then put `FHIR_SERVER_URL=http://localhost:7070/fhir` in your `.env`
   - N8N_AGENT_URL is the N8N agent workflow's production URL
   - N8N_EXECUTION_URL is the N8N workflow URL to generate execution logs

2. Install the required dependencies:
   - `requirements.txt`

3. Execute `run_eval.py` to run all experiments:
   - set up `run_eval.yaml` to specify the experiments and validation logics.




