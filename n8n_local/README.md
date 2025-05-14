# Local n8n Setup

This folder contains everything you need to **spin up** a local n8n instance for testing, along with a simple script to **import** existing workflows (in JSON format).

## Purpose

1. **Spin up** a local n8n environment quickly (using Docker Compose).
2. **Mount** a folder of JSON workflows to the container (`workflows/`).
3. **Easily import** those workflows into n8n using an automated script.

---

## Quick Start
### 1. Start the container
```bash
docker-compose up -d
```

### 2. Make the script executable (only needed once)
```bash
chmod +x import-workflows.sh
```

### 3. Run the import script
```bash
./import-workflows.sh
```

After startup, open http://localhost:5678 in your browser.

Use the credentials specified in docker-compose.yml (default: admin / some_password).

---

## Other Useful Commands
### View logs in real-time
```bash
docker-compose logs -f
```
Watch the n8n container’s output for debugging or confirmation.

### Stop the container (but keep data)
```bash
docker-compose down
```

### Remove everything (including data)
```bash
docker-compose down -v
```