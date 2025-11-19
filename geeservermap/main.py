"""This module contains the main function to run the geeservermap Flask app."""

# from dotenv import load_dotenv
import argparse
import uuid

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit

MESSAGES = {}

# load_dotenv()  # Load environment variable from .env
PORT = 8018
WIDTH = 800
HEIGHT = 600

parser = argparse.ArgumentParser()
parser.add_argument(
    "--port", default=PORT, help=f"Port in which the app will run. Defaults to {PORT}"
)
parser.add_argument(
    "--width", default=WIDTH, help=f"Width of the map's pane. Defaults to {WIDTH} px"
)
parser.add_argument(
    "--height",
    default=HEIGHT,
    help=f"Height of the map's pane. Defaults to {HEIGHT} px",
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')  # uses eventlet/gevent if installed


@socketio.on('connect')
def _on_connect():
    """Handle a new client connection."""
    print('Client connected:', request.sid)


def register_map(width, height, port=PORT):
    """Register the index endpoint, allowing the user to pass a height and width."""

    @app.route("/")
    def map():
        return render_template("map.html", width=width, height=height, port=port)


@app.route("/add_layer", methods=["GET"])
def add_layer():
    """Endpoint to add a layer to the map."""
    url = request.args.get("url", type=str)
    name = request.args.get("name", type=str)
    visible = request.args.get("visible", type=bool)
    opacity = request.args.get("opacity", type=float)
    layer = {"url": url, "name": name, "visible": visible, "opacity": opacity}
    job_id = uuid.uuid4().hex
    MESSAGES[job_id] = layer
    # broadcast full state to all connected websocket clients
    try:
        socketio.emit("messages", MESSAGES)
    except Exception as exc:
        print("socketio emit error:", exc)

    return jsonify({"job_id": job_id})


@app.route("/get_message", methods=["GET"])
def get_message():
    """Endpoint to retrieve a message by its job ID."""
    job_id = request.args.get("id", type=str)
    return jsonify(MESSAGES.get(job_id))


@app.route("/messages")
def messages():
    """Endpoint to retrieve all messages."""
    return jsonify(MESSAGES)


def run():
    """Run the Flask app."""
    args = parser.parse_args()
    port = args.port
    register_map(width=args.width, height=args.height, port=port)
    socketio.run(app, debug=True, port=port)
