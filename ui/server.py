from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Enable CORS for /route_message, /receive_reply, etc.
CORS(app)

# Track connected clients and session state
clients = {}
session_state = {}  # Stores sessionId -> last responding agent

AGENT_WEBHOOKS = {
    "frontdesk_agent": "https://congliu.app.n8n.cloud/webhook/413ab7a1-30ae-4276-a5d0-8d5ecda4f7a3",
    "education_agent": "https://congliu.app.n8n.cloud/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6"
}

@app.route('/')
def index():
    # If you still want to serve your old index.html (non-React),
    # keep this as is, or remove if you no longer use it.
    return render_template('index.html')


@app.route('/route_message', methods=['POST'])
def route_message():
    data = request.json
    session_id = data.get("sessionId")
    message = data.get("message")

    print(f"Received /route_message for session {session_id}, message={message}")

    # Get last responding agent or default to frontdesk
    agent = session_state.get(session_id, "frontdesk_agent")
    webhook_url = AGENT_WEBHOOKS.get(agent)

    if not webhook_url:
        print(f"Error: Unknown agent for session {session_id}")
        return "Unknown agent", 400

    print(f"Routing message from {session_id} to {agent} at {webhook_url}")

    try:
        response = requests.post(webhook_url, json={
            "sessionId": session_id,
            "message": message
        })
        print(f"Agent webhook responded with status {response.status_code}: {response.text}")
        return "Routed", 200
    except Exception as e:
        print(f"Exception calling agent webhook: {e}")
        return str(e), 500


@app.route('/receive_reply', methods=['POST'])
def receive_reply():
    data = request.json
    session_id = data.get('sessionId')
    message = data.get('reply')
    responding_agent = data.get('responding_agent')

    print(f"Received /receive_reply for session {session_id}, agent={responding_agent}, message={message}")

    # Update session state (which agent is now handling future messages)
    if responding_agent:
        session_state[session_id] = responding_agent

    # Check if this user is connected
    if session_id in clients:
        # Emit to user via Socket.IO
        socketio.emit('reply', {
            'message': message,
            'responding_agent': responding_agent
        }, room=clients[session_id])
        print(f"Delivered message to session {session_id}")
        return 'Delivered', 200

    print(f"No user connected for session {session_id}")
    return 'User not connected', 404


@socketio.on('connect')
def handle_connect():
    print("Client connected (Socket.IO)")


@socketio.on('register')
def handle_register(data):
    session_id = data.get('sessionId')
    clients[session_id] = request.sid
    print(f"Registered session: {session_id} -> {request.sid}")


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    to_remove = None
    for s_id, client_sid in clients.items():
        if client_sid == sid:
            to_remove = s_id
            break

    if to_remove:
        del clients[to_remove]
        print(f"Client disconnected: session {to_remove}")
    else:
        print("Client disconnected, but no matching session found")


if __name__ == '__main__':
    print("Starting")
    socketio.run(app, host='0.0.0.0', port=8000)
