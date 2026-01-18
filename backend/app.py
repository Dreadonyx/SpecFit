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
    # Map technical names to user-friendly names
    NAME_MAPPING = {
        'code': 'vscode',
        'chrome': 'chrome',
        'chromium': 'chrome',
        'java': 'java',
        'python': 'python',
        'python3': 'python',
        'node': 'nodejs',
        'docker': 'docker',
        'slack': 'slack',
        'teams': 'teams',
        'zoom': 'zoom'
    }
    
    processes = []
    for p in psutil.process_iter(['name', 'exe', 'memory_info']):
        try:
            mem_gb = p.info['memory_info'].rss / (1024 ** 3)
            
            # Try to get the executable name from the path
            exe_path = p.info.get('exe')
            if exe_path:
                # Extract just the executable name (e.g., "firefox-esr" from "/usr/lib/firefox-esr/firefox-esr")
                import os
                exe_name = os.path.basename(exe_path)
                # Clean up common suffixes
                if exe_name.endswith('-esr'):
                    exe_name = exe_name.replace('-esr', '')
                process_name = exe_name
            else:
                # Fallback to process name
                process_name = p.info['name'] or "unknown"
            
            # Apply friendly name mapping
            process_name = NAME_MAPPING.get(process_name.lower(), process_name)
            
            processes.append({
                "name": process_name,
                "memory_gb": round(mem_gb, 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not processes:
        return {"name": "unknown", "memory_gb": 0}

    return max(processes, key=lambda x: x["memory_gb"])

def get_verdict(cpu, memory):
    if memory < 70:
        return "NORMAL"
    if memory < 85:
        return "STRAINED"
    return "OVERLOADED"

def get_ai_insight(verdict, cpu, memory, top_proc, top_mem):
    # Always call Gemini AI for insights, regardless of verdict
    
    prompt = f"""
CRITICAL INSTRUCTION: You must output EXACTLY 3 numbered lines. Nothing else.

System status: {verdict}
Problem: {top_proc} using {top_mem}GB ({memory}% memory total)

Your output must be EXACTLY this format:
1. [process name] is using high memory.
2. Close [process name] if not in use or restart.
3. Refresh status again to check.

CORRECT example (use this exact structure):
1. firefox is using high memory.
2. Close firefox if not in use or restart.
3. Refresh status again to check.

WRONG formats (DO NOT use):
- firefox: monitor usage
- Close tabs
- firefox is heavy

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
        if not candidates:
            return f"1. {top_proc} is using high memory.\n2. Close {top_proc} if not in use or restart.\n3. Refresh status again to check."

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        texts = []
        for p in parts:
            t = p.get("text")
            if t:
                texts.append(t.strip())

        text = " ".join(texts)

        if not text:
            return f"1. {top_proc} is using high memory.\n2. Close {top_proc} if not in use or restart.\n3. Refresh status again to check."

        return text
    
    except Exception as e:
        # If there's any error, just note it in the response
        return f"1. Error getting AI insight: {str(e)[:30]}\n2. Check API connection.\n3. Refresh status again to check."


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
