# SpecFit 

> System health monitor that tells you the truth about how your machine is doing.

Not just CPU and RAM percentages — SpecFit classifies your system into one of three states and gives you a plain-language explanation of what's happening.

## Health states

| State | What it means |
|---|---|
| 🟢 NORMAL | All good |
| 🟡 STRAINED | Under pressure, watch it |
| 🔴 OVERLOADED | Something needs attention |

## Features

- Real-time CPU + memory monitoring via psutil
- AI explains what's happening in plain language
- Uses Ollama locally by default — falls back to Gemini if Ollama isn't running
- Non-blocking: metrics load instantly, AI explanation loads separately

## Run

```bash
git clone https://github.com/Dreadonyx/SpecFit
cd SpecFit/specfit/specfit_v2/backend
pip install flask psutil
python app.py
```

Open `http://localhost:5000`.

## Stack

- Python / Flask
- psutil
- Ollama (local AI, primary)
- Gemini API (cloud fallback)
- Vanilla HTML/CSS/JS
