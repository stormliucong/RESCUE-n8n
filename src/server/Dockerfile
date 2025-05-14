# Use a lightweight Python image as the base
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Flask app and dependency list into the container
COPY server.py requirements.txt ./

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose port 8000 to the host machine
EXPOSE 8000

# Command to run the Flask server when the container starts
CMD ["python", "server.py"]
