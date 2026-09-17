"""
app.py

Flask backend for the Hotel Recommendation Chatbot.
Serves the chat UI and proxies chat messages to the Gemini API.
"""

import os

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

from chatbot_config import SYSTEM_PROMPT, MODEL_NAME

# Load environment variables from .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Please add it to your .env file."
    )

genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# Create the Gemini model once, with the chatbot's system prompt.
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=SYSTEM_PROMPT,
)

# In-memory chat sessions, keyed by a simple session id from the client.
# Note: this resets whenever the server restarts.
chat_sessions = {}


def get_chat_session(session_id: str):
    """Return an existing chat session or create a new one."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = model.start_chat(history=[])
    return chat_sessions[session_id]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or "default"

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        chat_session = get_chat_session(session_id)
        response = chat_session.send_message(user_message)
        reply_text = response.text
    except Exception as exc:
        return jsonify({"error": f"Failed to get a response: {exc}"}), 500

    return jsonify({"reply": reply_text})


if __name__ == "__main__":
    app.run(debug=True)
