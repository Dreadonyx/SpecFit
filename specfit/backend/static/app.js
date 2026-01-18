const cpuEl = document.getElementById("cpu");
const memoryEl = document.getElementById("memory");
const verdictEl = document.getElementById("verdict");
const explanationEl = document.getElementById("explanation");

const cpuBar = document.getElementById("cpu-bar");
const memoryBar = document.getElementById("memory-bar");

function setVerdictColor(verdict) {
  if (verdict === "NORMAL") verdictEl.style.color = "#22C55E";
  else if (verdict === "STRAINED") verdictEl.style.color = "#F59E0B";
  else if (verdict === "OVERLOADED") verdictEl.style.color = "#EF4444";
}

function getFallbackExplanation(verdict) {
  if (verdict === "NORMAL") {
    return "System is healthy. No additional insights required at this time.";
  }
  if (verdict === "STRAINED") {
    return "System resources are under moderate pressure. Monitoring is recommended.";
  }
  if (verdict === "OVERLOADED") {
    return "System memory usage is critically high. Performance may degrade under sustained load.";
  }
  return "Using system-based analysis.";
}

function loadStatus() {
  fetch("/status")
    .then(res => res.json())
    .then(data => {
      const cpu = Number(data.cpu_usage.toFixed(1));
      const memory = Number(data.memory_usage.toFixed(1));

      cpuEl.innerText = cpu + "%";
      memoryEl.innerText = memory + "%";

      cpuBar.style.width = cpu + "%";
      memoryBar.style.width = memory + "%";

      verdictEl.innerText = data.verdict;
      setVerdictColor(data.verdict);

      explanationEl.innerText = "Analyzing…";

      fetch("/ai_explanation")
        .then(res => res.json())
        .then(aiData => {
          explanationEl.innerText =
            aiData.explanation || getFallbackExplanation(data.verdict);
        })
        .catch(() => {
          explanationEl.innerText = getFallbackExplanation(data.verdict);
        });
    })
    .catch(() => {
      cpuEl.innerText = "--%";
      memoryEl.innerText = "--%";

      cpuBar.style.width = "0%";
      memoryBar.style.width = "0%";

      verdictEl.innerText = "UNKNOWN";
      verdictEl.style.color = "#9CA3AF";

      explanationEl.innerText = "Unable to fetch system status.";
    });
}

loadStatus();
