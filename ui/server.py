"""
Multi‑agent Router / Evaluation Proxy
GUI: real‑time WebSocket chat routing
EVAL: one‑shot proxy to Scheduler Agent
ALL: both
"""

import os
import argparse
import requests
from flask import Flask, request, Response
from flask_cors import CORS

# -- Parse run‑mode ---------------------------------------------------------
parser = argparse.ArgumentParser(description="Run the server in GUI, EVAL or ALL mode")
parser.add_argument("--mode", choices=["GUI", "EVAL", "ALL"], default=os.getenv("SERVER_MODE", "ALL"))
MODE = parser.parse_args().mode.upper()

# -- Flask app + (optional) Socket.IO --------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
CORS(app)

socketio = None  # injected only for GUI/ALL
if MODE in ("GUI", "ALL"):
    from flask_socketio import SocketIO, emit
    socketio = SocketIO(app, cors_allowed_origins="*")

# -- In‑memory chat state ---------------------------------------------------
clients: dict[str, str] = {}          # sessionId -> socket SID
session_state: dict[str, str] = {}    # sessionId -> last agent

AGENT_WEBHOOKS = {
    "scheduler_agent": "https://congliu.app.n8n.cloud/webhook/b118593b-9350-40cf-a6a9-d1e3494da1c2",
    "frontdesk_agent": "https://congliu.app.n8n.cloud/webhook/413ab7a1-30ae-4276-a5d0-8d5ecda4f7a3",
    "education_agent": "https://congliu.app.n8n.cloud/webhook/bdfcc15d-a70c-4fb4-9df6-5beaf18fa2d6",
}

# -- Healthcheck ------------------------------------------------------------
@app.route("/")
def index():
    return f"Server running in {MODE} mode"

# -- GUI endpoints ----------------------------------------------------------
if MODE in ("GUI", "ALL"):

    @app.route("/route_message", methods=["POST"])
    def route_message():
        data = request.get_json(force=True, silent=True) or {}
        session_id = data.get("sessionId")
        message = data.get("message")
        if not session_id or message is None:
            return {"error": "sessionId and message required"}, 400

        agent = session_state.get(session_id, "frontdesk_agent")
        webhook = AGENT_WEBHOOKS.get(agent)
        if webhook is None:
            return {"error": f"Unknown agent '{agent}'"}, 400

        try:
            rsp = requests.post(webhook, json={"sessionId": session_id, "message": message})
            print(f"→ {agent} {rsp.status_code}")
            return "Routed", 200
        except requests.RequestException as e:
            return {"error": str(e)}, 502

    @app.route("/receive_reply", methods=["POST"])
    def receive_reply():
        data = request.get_json(force=True, silent=True) or {}
        session_id = data.get("sessionId")
        reply = data.get("reply")
        agent = data.get("responding_agent")
        if agent:
            session_state[session_id] = agent

        sid = clients.get(session_id)
        if sid and socketio:
            socketio.emit("reply", {"message": reply, "responding_agent": agent}, room=sid)
            return "Delivered", 200
        return "User not connected", 404

    # -- Socket.IO events ---------------------------------------------------
    @socketio.on("connect")
    def on_connect():
        print("socket connect")

    @socketio.on("register")
    def on_register(data):
        clients[data.get("sessionId")] = request.sid

    @socketio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        for s_id, client_sid in list(clients.items()):
            if client_sid == sid:
                del clients[s_id]
                break

# -- Evaluation proxy -------------------------------------------------------
if MODE in ("EVAL", "ALL"):

    @app.route("/eval/scheduler", methods=["POST"])
    def eval_scheduler_proxy():
        payload = request.get_json(force=True, silent=True) or {}
        try:
            rsp = requests.post(
                AGENT_WEBHOOKS["scheduler_agent"],
                json=payload,
                timeout=int(os.getenv("EVAL_PROXY_TIMEOUT", 30)),
            )
            rsp.raise_for_status()
        except requests.exceptions.Timeout:
            return {"error": "Scheduler Agent timed out"}, 504
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}, 502

        execution_id = rsp.headers.get("execution_id")
        proxy_response = Response(rsp.content, status=rsp.status_code, content_type=rsp.headers.get("Content-Type", "application/json"))
        if execution_id:
            proxy_response.headers["execution_id"] = execution_id
        return proxy_response

# -- Entrypoint -------------------------------------------------------------
if __name__ == "__main__":
    print(f"Starting {MODE} server :8000")
    if MODE in ("GUI", "ALL") and socketio:
        socketio.run(app, host="0.0.0.0", port=8000)
    else:
        app.run(host="0.0.0.0", port=8000)
