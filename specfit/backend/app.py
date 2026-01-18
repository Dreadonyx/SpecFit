import os
import requests
import psutil
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

NORMAL_MESSAGE = "System stable. No action needed."

def get_verdict(cpu, memory):
    if memory < 70:
        return "NORMAL"
    if memory < 85:
        return "STRAINED"
    return "OVERLOADED"

def get_ai_insight(verdict, cpu, memory):
    if verdict == "NORMAL":
        return NORMAL_MESSAGE

    prompt = f"""
Write ONE short system insight.
Total length must be under 40 characters.
No punctuation at end.
No emojis.
No explanations.

CPU: {cpu}%
Memory: {memory}%
Verdict: {verdict}
"""

    response = requests.post(
        f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
        json={
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        },
        timeout=6
    )

    text = (
        response.json()
        .get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
        .strip()
    )

    if not text:
        return "System under memory pressure"

    return text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/status")
def status():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent

    verdict = get_verdict(cpu, memory)
    ai_insight = get_ai_insight(verdict, cpu, memory)

    return jsonify({
        "cpu_usage": round(cpu, 1),
        "memory_usage": round(memory, 1),
        "verdict": verdict,
        "ai_insight": ai_insight
    })

if __name__ == "__main__":
    app.run(debug=True)
