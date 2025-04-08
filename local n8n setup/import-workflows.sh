#!/bin/bash

# import-workflows.sh
# This script will import all JSON files from the /home/node/workflows folder
# into the running n8n instance, treating each file as a separate workflow.

docker-compose exec n8n-service \
  n8n import:workflow \
  --separate \
  --input="/home/node/workflows"
