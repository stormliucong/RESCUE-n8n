#!/bin/bash

echo "Starting HAPI FHIR server restart process..."

# Stop and remove the containers
echo "Stopping and removing FHIR containers..."
docker-compose down

# Start the containers again
echo "Starting FHIR containers..."
docker-compose up -d

# Wait for the container to be healthy
echo "Waiting for FHIR server to be healthy (30 seconds)..."
sleep 30

# Check if the container is running
if docker ps | grep -q hapifhir; then
    echo "HAPI FHIR server successfully restarted!"
else
    echo "Error: FHIR container is not running. Please check the logs."
    docker-compose logs web
fi 