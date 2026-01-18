import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

NORMAL_MESSAGE = "System stable. No action needed."

def get_ai_insight(verdict, cpu, memory):
    if verdict == "NORMAL":
        char_limit = 20
        tone = "calm and reassuring"
    elif verdict == "STRAINED":
        char_limit = 30
        tone = "informative and neutral"
    else:
        char_limit = 40
        tone = "cautionary but not alarming"

    prompt = f"""
You are a system monitor.

Write a short structured insight.
Use 1 or 2 short lines or bullets.
Total characters MUST be under {char_limit}.
No punctuation at end.
No emojis.
No explanations.

Tone: {tone}

Context:
CPU {cpu} percent
Memory {memory} percent
State {verdict}

Return only the insight.
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
        return "System stable"

    return text

