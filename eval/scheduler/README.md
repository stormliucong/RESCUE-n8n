# Scheduler Module Evaluation

This module provides functionality for managing medical appointments and scheduling in a genetic healthcare system. It will evaluate a comprehensive scheduling agent that handles patient appointments, waitlists, and provider availability with interaction with a FHIR server

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

### Data Generation 
- `generate_schedule_sync_data.py`: Generates test data for the evaluation

### Scheduler Evaluation Scripts

   `[1-15]_*.py`: implement various healthcare scheduling and patient management scenarios. Each script is designed to work with a FHIR server and includes proper error handling and verification of results. Each script follows a consistent structure:

   1. **Evaluation Prompt**: Each file starts with a clear description of the task it's designed to evaluate
   2. **FHIR Resource Preparation**: Sets up necessary FHIR resources (Practitioners, Schedules, Slots, etc.)
   3. **Expected Actions**: Implements the core functionality and includes assertions to verify correct behavior

## Setup

1. Ensure you have the required environment variables set in `.env`
   - `FHIR_SERVER_URL`: The URL of your FHIR server
   - If you don't have a FHIR server, you can spin up a local one using `restart_fhir.sh`; 
   Then put `FHIR_SERVER_URL=http://localhost:7070/fhir` in your `.env`

2. Install the required dependencies:
   - requests
   - faker
   - python-dotenv





