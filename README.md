# RESCUE-n8n
This is a repo for storing the replicable self-hosted n8n workflow

## Get Started
### Set up 8n8 + fhir server following [this](https://bonfhir.dev/docs/build-workflows-with-n8n/setup-the-environment)

- No need for SMTP server now
- `docker compose up`

### Setup encryption
- created ${N8N_ENCRYPTION_KEY} to setup all credential from beginning
- bonfhir credential
    - Username: admin@example.com
    - Password: medplum_admin

- fhir basic auth
    - Username: f54370de-eaf3-4d81-a17e-24860f667912
    - Password: 75d8e7d06bf9283926c51d5f461295ccf0b69128e983b6ecdd5a9c07506895de

- Important: go to the userinterface to superconfig valuesets and search parameters and allow searching other resource type

### Import workflows to n8n



