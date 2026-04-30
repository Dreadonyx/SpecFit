const cpuEl = document.getElementById("cpu");
const memEl = document.getElementById("memory");
const verdictEl = document.getElementById("verdict");
const aiEl = document.getElementById("ai-insight");

const cpuBar = document.getElementById("cpu-bar");
const memBar = document.getElementById("memory-bar");

const usedEl = document.getElementById("mem-used");
const freeEl = document.getElementById("mem-free");
const availEl = document.getElementById("mem-avail");

const procNameEl = document.getElementById("proc-name");
const procMemEl = document.getElementById("proc-mem");

function setVerdictColor(v) {
  if (v === "NORMAL") verdictEl.style.color = "#22c55e";
  else if (v === "STRAINED") verdictEl.style.color = "#f59e0b";
  else verdictEl.style.color = "#ef4444";
}

function loadStatus() {
  aiEl.textContent = "Analyzing system…";

  fetch("/status")
    .then(res => res.json())
    .then(data => {
      cpuEl.textContent = data.cpu_usage + "%";
      memEl.textContent = data.memory_usage + "%";

      cpuBar.style.width = data.cpu_usage + "%";
      memBar.style.width = data.memory_usage + "%";

      verdictEl.textContent = data.verdict;
      setVerdictColor(data.verdict);

      usedEl.textContent = data.memory.used_gb;
      freeEl.textContent = data.memory.free_gb;
      availEl.textContent = data.memory.available_gb;

      procNameEl.textContent = data.top_process.name;
      procMemEl.textContent = data.top_process.memory_gb;

      aiEl.textContent = data.ai_insight;

    })
    .catch(() => {
      verdictEl.textContent = "ERROR";
      aiEl.textContent = "Unable to fetch system data";
    });
}

loadStatus();
document
  .getElementById("refresh-btn")
  .addEventListener("click", loadStatus);

