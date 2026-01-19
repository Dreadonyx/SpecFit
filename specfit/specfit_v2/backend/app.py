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

def get_top_memory_process():
    """Get the process using the most memory, aggregating by name."""
    from collections import defaultdict
    
    # Aggregate memory by process name
    memory_by_name = defaultdict(float)
    
    for p in psutil.process_iter(['name', 'exe', 'memory_info']):
        try:
            mem_gb = p.info['memory_info'].rss / (1024 ** 3)
            
            # Get exact executable name from path
            exe_path = p.info.get('exe')
            if exe_path:
                process_name = os.path.basename(exe_path)
            else:
                process_name = p.info['name'] or "unknown"
            
            # Sum memory for all processes with the same name
            memory_by_name[process_name] += mem_gb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not memory_by_name:
        return {"name": "unknown", "memory_gb": 0}

    # Find the process name with highest total memory
    top_name = max(memory_by_name, key=memory_by_name.get)
    return {"name": top_name, "memory_gb": round(memory_by_name[top_name], 2)}

def get_verdict(cpu, memory):
    if memory < 70:
        return "NORMAL"
    if memory < 85:
        return "STRAINED"
    return "OVERLOADED"

def get_ai_insight(verdict, cpu, memory, top_proc, top_mem):
    """Get AI insight from Gemini API only."""
    
    # For NORMAL status, return a simple stable message
    if verdict == "NORMAL":
        return "System stable. No action needed."
    
    prompt = f"""CRITICAL INSTRUCTION: You must output EXACTLY 3 numbered lines. Nothing else.

System status: {verdict}
Problem: {top_proc} using {top_mem}GB ({memory}% memory total)

Your output must be EXACTLY this format:
1. [process name] is using high memory.
2. Close [process name] if not in use or restart.
3. Refresh status again to check.

Output the 3 numbered lines now using the process: {top_proc}
"""

    try:
        response = requests.post(
            f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}",
            json={
                "contents": [
                    {"parts": [{"text": prompt}]}]
            }
        )
        
        data = response.json()
        candidates = data.get("candidates", [])
        
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            texts = [p.get("text", "").strip() for p in parts if p.get("text")]
            text = " ".join(texts)
            
            if text:
                return text
    except Exception:
        pass
    
    # Simple static fallback if Gemini fails (only for non-NORMAL states)
    return f"Memory at {memory}%. Consider closing {top_proc}."


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/status")
def status():
    cpu = psutil.cpu_percent(interval=1)

    mem = psutil.virtual_memory()
    memory_percent = mem.percent

    used_gb = round(mem.used / (1024 ** 3), 1)
    free_gb = round(mem.free / (1024 ** 3), 1)
    avail_gb = round(mem.available / (1024 ** 3), 1)

    verdict = get_verdict(cpu, memory_percent)

    top_proc = get_top_memory_process()

    ai_insight = get_ai_insight(
        verdict,
        cpu,
        memory_percent,
        top_proc["name"],
        top_proc["memory_gb"]
    )

    return {
        "cpu_usage": round(cpu, 1),
        "memory_usage": round(memory_percent, 1),
        "memory": {
            "used_gb": used_gb,
            "free_gb": free_gb,
            "available_gb": avail_gb
        },
        "top_process": top_proc,
        "verdict": verdict,
        "ai_insight": ai_insight
    }

if __name__ == "__main__":
    app.run(debug=True)
