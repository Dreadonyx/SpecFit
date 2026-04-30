// ── DOM References ──
const $ = id => document.getElementById(id);

// Gauges
const cpuRing = $("cpu-ring");
const memRing = $("mem-ring");
const swapRing = $("swap-ring");
const cpuText = $("cpu-text");
const memText = $("mem-text");
const swapText = $("swap-text");

// Gauge meta
const cpuCores = $("cpu-cores");
const cpuFreq = $("cpu-freq");
const memUsedTotal = $("mem-used-total");
const memAvailable = $("mem-available");
const swapUsedTotal = $("swap-used-total");

// System
const systemInfo = $("system-info");
const uptimeEl = $("uptime");
const verdictEl = $("verdict");
const aiInsight = $("ai-insight");

// Stats
const netStat = $("net-stat");
const diskIoStat = $("disk-io-stat");

const RING_SIZE = 326.73; // 2 * Math.PI * 52
const REFRESH_MS = 3000;

// ── Chart.js Defaults ──
Chart.defaults.color = "#9ca3af";
Chart.defaults.borderColor = "rgba(55,65,81,0.3)";
Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
Chart.defaults.font.size = 11;

const commonScales = {
  x: { display: false },
  y: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" }, grid: { color: "rgba(55,65,81,0.2)" } }
};

const makeLabels = n => Array.from({ length: n }, (_, i) => "");

function makeDataset(label, color, data = []) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: color.replace("1)", "0.1)"),
    fill: true,
    tension: 0.4,
    pointRadius: 0,
    borderWidth: 2,
  };
}

// ── Initialize Charts ──
const cpuChart = new Chart($("cpu-chart"), {
  type: "line",
  data: { labels: makeLabels(60), datasets: [makeDataset("CPU %", "rgba(34,211,238,1)")] },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { ...commonScales } },
});

const memChart = new Chart($("mem-chart"), {
  type: "line",
  data: {
    labels: makeLabels(60),
    datasets: [
      makeDataset("Memory %", "rgba(167,139,250,1)"),
      makeDataset("Swap %", "rgba(52,211,153,1)"),
    ],
  },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { boxWidth: 12, padding: 16 } } }, scales: { ...commonScales } },
});

const netChart = new Chart($("net-chart"), {
  type: "line",
  data: {
    labels: makeLabels(60),
    datasets: [
      makeDataset("Sent KB/s", "rgba(34,211,238,1)"),
      makeDataset("Recv KB/s", "rgba(251,146,60,1)"),
    ],
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { boxWidth: 12, padding: 16 } } },
    scales: {
      x: { display: false },
      y: { beginAtZero: true, ticks: { callback: v => v.toFixed(0) + " KB/s" }, grid: { color: "rgba(55,65,81,0.2)" } },
    },
  },
});

const diskIoChart = new Chart($("disk-io-chart"), {
  type: "line",
  data: {
    labels: makeLabels(60),
    datasets: [
      makeDataset("Read MB/s", "rgba(34,197,94,1)"),
      makeDataset("Write MB/s", "rgba(239,68,68,1)"),
    ],
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { boxWidth: 12, padding: 16 } } },
    scales: {
      x: { display: false },
      y: { beginAtZero: true, ticks: { callback: v => v.toFixed(1) + " MB/s" }, grid: { color: "rgba(55,65,81,0.2)" } },
    },
  },
});

let coreChart = null;

// ── Gauge helper ──
function setGauge(ring, textEl, percent, warnThresh = 70, dangerThresh = 85) {
  const offset = RING_SIZE - (RING_SIZE * Math.min(percent, 100)) / 100;
  ring.style.strokeDashoffset = offset;
  textEl.textContent = percent.toFixed(1) + "%";

  // Dynamic color
  if (!ring.classList.contains("memory-ring") && !ring.classList.contains("swap-ring")) {
    if (percent > dangerThresh) ring.style.stroke = "#ef4444";
    else if (percent > warnThresh) ring.style.stroke = "#f59e0b";
    else ring.style.stroke = "#22d3ee";
  }
}

// ── Verdict ──
function setVerdict(v) {
  verdictEl.textContent = v;
  verdictEl.className = "verdict-badge";
  if (v === "NORMAL") verdictEl.classList.add("verdict-normal");
  else if (v === "STRAINED") verdictEl.classList.add("verdict-strained");
  else verdictEl.classList.add("verdict-overloaded");
}

// ── Update Charts ──
function updateLineChart(chart, ...datasets) {
  const maxLen = Math.max(...datasets.map(d => d.length));
  chart.data.labels = makeLabels(maxLen);
  datasets.forEach((data, i) => {
    chart.data.datasets[i].data = data;
  });
  chart.update("none");
}

// ── Per-Core Chart ──
function updateCoreChart(coresData) {
  const coreCount = Object.keys(coresData).length;
  if (!coreCount) return;

  const labels = Object.keys(coresData).map(k => `Core ${k}`);
  const latest = Object.values(coresData).map(arr => arr.length ? arr[arr.length - 1] : 0);

  if (!coreChart) {
    const colors = latest.map((_, i) => {
      const hue = (i / coreCount) * 180 + 160;
      return `hsla(${hue}, 70%, 60%, 1)`;
    });
    const bgColors = colors.map(c => c.replace("1)", "0.25)"));

    coreChart = new Chart($("core-chart"), {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Usage %",
          data: latest,
          backgroundColor: bgColors,
          borderColor: colors,
          borderWidth: 1,
          borderRadius: 4,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%" }, grid: { color: "rgba(55,65,81,0.2)" } },
        },
      },
    });
  } else {
    coreChart.data.datasets[0].data = latest;
    coreChart.update("none");
  }
}

// ── Disk Partitions ──
function renderDisks(partitions) {
  const el = $("disk-list");
  if (!partitions.length) {
    el.innerHTML = '<span style="color:var(--text-dim);font-size:0.82rem;">No partitions detected</span>';
    return;
  }
  el.innerHTML = partitions.map(p => {
    const cls = p.percent > 90 ? "danger" : p.percent > 75 ? "warn" : "";
    return `
      <div class="disk-item">
        <div class="disk-item-header">
          <span>${p.mountpoint} <span style="color:var(--text-dim)">(${p.fstype})</span></span>
          <span>${p.used_gb} / ${p.total_gb} GB (${p.percent}%)</span>
        </div>
        <div class="disk-bar"><div class="disk-bar-fill ${cls}" style="width:${p.percent}%"></div></div>
      </div>
    `;
  }).join("");
}

// ── Processes ──
function renderProcesses(processes) {
  const tbody = $("proc-tbody");
  tbody.innerHTML = processes.map((p, i) => `
    <tr>
      <td style="color:var(--text-dim)">${i + 1}</td>
      <td><strong>${p.name}</strong></td>
      <td>
        <span class="proc-bar" style="width:${Math.min(p.memory_percent * 2, 100)}px"></span>
        ${p.memory_mb} MB
      </td>
      <td>${p.memory_percent}%</td>
      <td>${p.cpu_percent}%</td>
      <td style="color:var(--text-dim)">${p.instances}</td>
    </tr>
  `).join("");
}

// ── Temperatures ──
function renderTemps(temps) {
  const card = $("temp-card");
  const el = $("temp-list");
  const keys = Object.keys(temps);
  if (!keys.length) { card.style.display = "none"; return; }
  card.style.display = "";
  el.innerHTML = keys.map(k => {
    const v = temps[k];
    const cls = v > 85 ? "temp-hot" : v > 65 ? "temp-warm" : "temp-ok";
    return `<div class="temp-item"><span>${k}</span><span class="temp-value ${cls}">${v}°C</span></div>`;
  }).join("");
}

// ── Main Fetch ──
let isFirstLoad = true;

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const d = await res.json();

    // Gauges
    setGauge(cpuRing, cpuText, d.cpu.total);
    setGauge(memRing, memText, d.memory.percent);
    setGauge(swapRing, swapText, d.swap.percent);

    // Gauge meta
    cpuCores.textContent = `${d.cpu.physical_cores}C / ${d.cpu.core_count}T`;
    cpuFreq.textContent = d.cpu.freq_mhz ? `${d.cpu.freq_mhz.toFixed(0)} MHz` : "—";
    memUsedTotal.textContent = `${d.memory.used_gb} / ${d.memory.total_gb} GB`;
    memAvailable.textContent = `${d.memory.available_gb} GB avail`;
    swapUsedTotal.textContent = `${d.swap.used_gb} / ${d.swap.total_gb} GB`;

    // System
    systemInfo.textContent = `${d.system.hostname} · ${d.system.os}`;
    uptimeEl.textContent = `⏱ ${d.system.uptime}`;

    // Verdict + AI
    setVerdict(d.verdict);
    aiInsight.textContent = d.ai_insight;

    // Charts
    updateLineChart(cpuChart, d.cpu.history);
    updateLineChart(memChart, d.memory.history, d.swap.history);
    updateLineChart(netChart, d.network.sent_history, d.network.recv_history);
    updateLineChart(diskIoChart, d.disk.io.read_history, d.disk.io.write_history);
    updateCoreChart(d.cpu.per_core_history);

    // Stats
    netStat.textContent = `↑ ${d.network.sent_kb_s} KB/s   ↓ ${d.network.recv_kb_s} KB/s   🔗 ${d.network.connections}`;
    diskIoStat.textContent = `R: ${d.disk.io.read_mb_s} MB/s   W: ${d.disk.io.write_mb_s} MB/s`;

    // Panels
    renderDisks(d.disk.partitions);
    renderProcesses(d.processes);
    renderTemps(d.temperatures);

    // Pulse animation on update (skip first load)
    if (!isFirstLoad) {
      document.querySelectorAll(".card").forEach(c => {
        c.classList.remove("updating");
        void c.offsetWidth; // reflow trigger
        c.classList.add("updating");
      });
    }
    isFirstLoad = false;

  } catch (e) {
    verdictEl.textContent = "ERROR";
    verdictEl.className = "verdict-badge verdict-overloaded";
    aiInsight.textContent = "Unable to fetch system data. Is the backend running?";
  }
}

// ── Start ──
fetchStatus();
setInterval(fetchStatus, REFRESH_MS);
