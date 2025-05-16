# RESCUE-n8n

## Project Overview
This project is a modular, multi-agent chat system built to support patients, primary care providers (PCPs), and genetic counselors in navigating the diagnosis and management of genetic disorders and rare diseases. It features a real-time, AI-powered chat interface built with React, connected to a Flask backend that routes messages between users and specialized agents such as Front Desk, Education, Scheduling, and Administrative. Each agent handles a specific part of the clinical workflow and can refer the conversation to another agent when appropriate, much like how referrals work in a real clinical setting. Agent logic is managed through n8n workflows, making the system easy to test, adapt, and extend. It supports both live interactions and automated evaluations, with the overall goal of streamlining triage and improving access to genetic care.

## Repo Folder Structure
- `.github/workflows/`
    - `deploy-to-droplet.yml`: Github Action to automatically redeploy the Chat UI to a remote droplet server whenever changes are pushed to `src/chat-ui-react/` on the `main branch`, or when triggered manually
    - `sync-n8n-workflows.yml`: Github Action to Sync the `n8n_local/workflows/` folder daily with the latest workflows from the remote n8n instance.

- `db/`
    - `insurance_policy`: Insurance policies related to genetic testing for major insurance providers in the US.

- `eval/`
    - `scheduler/`: Evaluation pipeline for the *Scheduling Agent*
        - `tasks/`: List of tailored evaluation scenarios for the *Scheduling Agent*, implementing the `task_interface.py` interface.
        - `fhir-server/`: Setup for running a local HAPI FHIR server (containerized).
        - `task_interface.py`: An interface implemented by the evaluation tasks for the *Scheduling Agent*.
        - `run_eval.py`: Script to load, execute, and evaluate *Scheduling Agent* tasks.
        - `run_eval.yaml`: Configuration file listing evaluation task modules, classes, requirements, and parameters for automated agent evaluation.
    - `education/`: Evaluation pipeline for the *Education Agent*.
    - `insurance/`: Evaluation pipeline for the *Insurance Agent*.

- `n8n_local/`
    - `workflows/`: An up-to-date list of n8n workflows in the form of JSON files (per-workflow documentation is available here: [Workflows documentation](n8n_local/n8n-workflows-documentation.md))
    - `docker-compose.yml`: A docker compose file to spin up a local n8n instance container.
    - `import-workflows.sh`: A script to automatically populate the local n8n instance with the JSON workflows in `n8n_local/workfows/`.

- `src/`: Source code for running the multi-agent system.
    - `.env`
    - `chat-ui-react/`: React-based chat GUI for running the multi-agent system.
    - `nginx/`: Config files to set up Nginx as a reverse proxy for the app.
    - `server/`
        - `prompts/`: List of system prompts for n8n agents.
        - `server.py`: A Python FLask server to handle one-shot evaluations for n8n agents, multi-turn evaluations, and the routing logic related to the chat GUI.
    - `test.sh`: Script to perform a health check/ping on the server.



