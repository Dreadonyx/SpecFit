# SpecFit

SpecFit is a lightweight system health monitor that evaluates CPU and memory usage
and reports whether a system is operating normally for its current specifications.

## Features
- Real-time CPU & memory monitoring
- Clear health verdict (NORMAL / STRAINED / OVERLOADED)
- Optional AI-based explanation (local-first via Ollama, cloud fallback)
- Non-blocking architecture (system metrics never wait on AI)

## Tech Stack
- Python (Flask)
- psutil
- Vanilla HTML/CSS/JS
- Ollama (local AI)
- Gemini (optional cloud AI)

## Why SpecFit?
SpecFit focuses on **honest system health**, not vanity metrics.
AI is used as an assistant, not a dependency.

## Run Locally
```bash
cd backend
python app.py
