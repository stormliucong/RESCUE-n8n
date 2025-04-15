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
- Waiver processing

## Components

### Start FHIR 
- `restart_fhir.sh`: start FHIR server for evaluation
- `docker-composer.yaml`: Docker container to start a fhir server

### Core Scheduling
- `23_make_appointment.py`: Handles appointment creation
- `24_cancel_appointment.py`: Manages appointment cancellations
- `25_search_appointment_detail.py`: Retrieves appointment details
- `15-18_find_slot_on_provider.py`: Finds available slots for specific providers
- `19-21_find_slot_on_time.py`: Finds available slots within specific time ranges
- `22_find_patient_from_slot.py`: Retrieves patient information from a slot

### Patient Management
- `1_new_patient_test.py`: Creates new patient records
- `2+3_verify_patient_test.py`: Verifies patient information
- `4_enter_medical_history.py`: Records patient medical history
- `5_search_medical_history.py`: Retrieves medical history
- `8_enter_insurance.py`: Manages insurance information
- `9_search_insurance.py`: Searches insurance records

### Waitlist Management
- `28_add_to_wailist.py`: Adds patients to waitlist
- `29+30_remove_waitlist.py`: Removes patients from waitlist

### Guarantor and Waiver Management
- `10_search_guarantor.py`: Searches guarantor information
- `11_add_guarantor.py`: Adds new guarantor records
- `13_create_waiver.py`: Creates waiver documents
- `14_search_waiver.py`: Searches waiver records

### Data Generation
- `generate_schedule_sync_data.py`: Generates test data for the evaluation

## Setup

1. Ensure you have the required environment variables set in `.env`
   - `FHIR_SERVER_URL`: The URL of your FHIR server
   - If you don't have a FHIR server, you can spin up a local one using `restart_fhir.sh`; 
   Then put `FHIR_SERVER_URL=http://localhost:7070/fhir` in your `env`

2. Install the required dependencies:
   - requests
   - faker
   - python-dotenv

## Usage

The module is designed to work with a FHIR-compliant server. Each script can be run independently to perform specific scheduling operations. The `generate_schedule_sync_data.py` script can be used to populate the system with test data. *Attention: this script will delete all relevant resources on your FHIR server.*

## Testing

The module includes various test scripts that can be used to verify the functionality of different components. Each test script is numbered and focuses on a specific aspect of the scheduling system.

## Notes

- All operations are performed using FHIR REST API
- The system maintains data consistency through proper resource linking
- Error handling and validation are implemented throughout the module
