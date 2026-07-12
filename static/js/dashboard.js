/**
 * dashboard.js
 * Fetches all monitoring endpoints on a 2s interval and updates the DOM,
 * charts, and status indicators. No page reloads — pure fetch + DOM patch.
 */

const REFRESH_MS = 2000;
let charts = {};
let lastOverallStatus = null;
let lastDockerAvailable = null;

document.addEventListener("DOMContentLoaded", () => {
  charts = initCharts();
  setupNav();
  setupThemeToggle();
  setupSidebarToggle();
  setupProcessSearch();
  setupExportButtons();

  refreshAll();
  setInterval(refreshAll, REFRESH_MS);

  setTimeout(() => document.getElementById("boot-overlay").classList.add("hidden"), 700);
});

/* ---------------- Fetch orchestration ---------------- */

async function fetchJSON(url) {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${url} responded ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Fetch failed:", url, err);
    return null;
  }
}

async function refreshAll() {
  const [summary, cpu, memory, disk, network, docker, processes, load] = await Promise.all([
    fetchJSON("/api/summary"),
    fetchJSON("/api/cpu"),
    fetchJSON("/api/memory"),
    fetchJSON("/api/disk"),
    fetchJSON("/api/network"),
    fetchJSON("/api/docker"),
    fetchJSON("/api/processes"),
    fetchJSON("/api/load"),
  ]);

  if (summary) updateSummary(summary);
  if (cpu) updateCpu(cpu);
  if (memory) updateMemory(memory);
  if (disk) updateDisk(disk);
  if (network) updateNetwork(network);
  if (docker) updateDocker(docker);
  if (processes) updateProcesses(processes.processes);
  if (load) updateLoad(load);

  fetchJSON("/api/system").then((data) => data && updateSystemInfo(data));
}

/* ---------------- Summary / overview ---------------- */

const STATUS_ICON = {
  healthy: '<i class="bi bi-check-circle-fill"></i>',
  warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
  critical: '<i class="bi bi-x-octagon-fill"></i>',
};

function statusBadgeClass(status) {
  return { healthy: "badge-healthy", warning: "badge-warning", critical: "badge-critical" }[status] || "badge-healthy";
}

function updateSummary(summary) {
  const pill = document.getElementById("overall-status-pill");
  const dot = pill.querySelector(".status-dot");
  const text = document.getElementById("overall-status-text");
  dot.className = `status-dot ${summary.overall_status}`;
  text.textContent = summary.overall_status.charAt(0).toUpperCase() + summary.overall_status.slice(1);

  if (lastOverallStatus && lastOverallStatus !== summary.overall_status && summary.overall_status !== "healthy") {
    showToast(
      `System status changed to ${summary.overall_status.toUpperCase()}`,
      summary.overall_status
    );
  }
  lastOverallStatus = summary.overall_status;

  const cards = [
    { icon: "bi-cpu-fill", label: "CPU Usage", value: `${summary.cpu_percent}%`, status: summary.cpu_status },
    { icon: "bi-memory", label: "Memory Usage", value: `${summary.memory_percent}%`, status: summary.memory_status },
    { icon: "bi-device-hdd-fill", label: "Disk Usage", value: `${summary.disk_percent}%`, status: summary.disk_status },
    { icon: "bi-hexagon-fill", label: "Uptime", value: summary.uptime, status: "healthy" },
    { icon: "bi-box-seam-fill", label: "Docker Containers", value: summary.docker_available ? summary.docker_running_containers : "N/A", status: summary.docker_available ? "healthy" : "warning" },
    { icon: "bi-hdd-fill", label: "Hostname", value: summary.hostname, status: "healthy" },
  ];

  const container = document.getElementById("summary-cards");
  container.innerHTML = cards
    .map(
      (c) => `
      <div class="col-xl-2 col-md-4 col-6">
        <div class="glass-card summary-card">
          <span class="summary-badge ${statusBadgeClass(c.status)}">${c.status}</span>
          <div class="summary-icon" style="background:rgba(34,211,238,.1); color:var(--accent-cyan)"><i class="bi ${c.icon}"></i></div>
          <span class="summary-label">${c.label}</span>
          <span class="summary-value">${c.value}</span>
        </div>
      </div>`
    )
    .join("");
}

/* ---------------- CPU ---------------- */

function updateCpu(cpu) {
  document.getElementById("cpu-usage").textContent = `${cpu.usage_percent}%`;
  document.getElementById("cpu-cores-logical").textContent = cpu.core_count_logical ?? "N/A";
  document.getElementById("cpu-cores-physical").textContent = cpu.core_count_physical ?? "N/A";
  document.getElementById("cpu-freq").textContent = cpu.frequency_current_mhz ? `${Math.round(cpu.frequency_current_mhz)} MHz` : "N/A";
  document.getElementById("cpu-chart-value").textContent = `${cpu.usage_percent}%`;

  updateSingleChart(charts.cpuChart, cpu.usage_percent);

  const grid = document.getElementById("per-core-container");
  grid.innerHTML = (cpu.per_core || [])
    .map(
      (val, idx) => `
      <div class="core-chip">
        <div class="core-label">CORE ${idx}</div>
        <div class="core-val">${val}%</div>
        <div class="progress-track"><div class="progress-fill ${progressClass(val, 75, 90)}" style="width:${val}%"></div></div>
      </div>`
    )
    .join("");
}

function updateLoad(load) {
  const l1 = load.load_1min ?? "N/A";
  const l5 = load.load_5min ?? "N/A";
  const l15 = load.load_15min ?? "N/A";
  document.getElementById("cpu-load").textContent = `${l1} / ${l5} / ${l15}`;

  const temp = load.temperature;
  document.getElementById("cpu-temp").textContent =
    temp && temp.available ? `${temp.temperature_c}°C` : "N/A";
}

/* ---------------- Memory ---------------- */

function updateMemory(memory) {
  document.getElementById("ram-total").textContent = memory.total;
  document.getElementById("ram-used").textContent = memory.used;
  document.getElementById("ram-available").textContent = memory.available;
  document.getElementById("ram-percent").textContent = `${memory.percent}%`;
  document.getElementById("ram-chart-value").textContent = `${memory.percent}%`;

  const ramFill = document.getElementById("ram-progress");
  ramFill.style.width = `${memory.percent}%`;
  ramFill.className = `progress-fill ${progressClass(memory.percent, 75, 90)}`;

  updateSingleChart(charts.ramChart, memory.percent);

  const swap = memory.swap || {};
  document.getElementById("swap-total").textContent = swap.total ?? "N/A";
  document.getElementById("swap-used").textContent = swap.used ?? "N/A";
  document.getElementById("swap-free").textContent = swap.free ?? "N/A";
  document.getElementById("swap-percent").textContent = `${swap.percent ?? 0}%`;
  const swapFill = document.getElementById("swap-progress");
  swapFill.style.width = `${swap.percent ?? 0}%`;
  swapFill.className = `progress-fill ${progressClass(swap.percent ?? 0, 75, 90)}`;
}

/* ---------------- Disk ---------------- */

function updateDisk(disk) {
  document.getElementById("disk-total").textContent = disk.total;
  document.getElementById("disk-used").textContent = disk.used;
  document.getElementById("disk-free").textContent = disk.free;
  document.getElementById("disk-percent").textContent = `${disk.percent}%`;
  document.getElementById("disk-chart-value").textContent = `${disk.percent}%`;

  const diskFill = document.getElementById("disk-progress");
  diskFill.style.width = `${disk.percent}%`;
  diskFill.className = `progress-fill ${progressClass(disk.percent, 80, 90)}`;

  updateSingleChart(charts.diskChart, disk.percent);

  const tbody = document.getElementById("partitions-table-body");
  tbody.innerHTML = (disk.partitions || [])
    .map(
      (p) => `
      <tr>
        <td>${p.device}</td>
        <td>${p.mountpoint}</td>
        <td>${p.fstype}</td>
        <td>${p.total}</td>
        <td>${p.used}</td>
        <td><span class="pill-status ${statusBadgeClass(progressClass(p.percent, 80, 90, true))}">${p.percent}%</span></td>
      </tr>`
    )
    .join("") || `<tr><td colspan="6" class="text-center text-muted">No partitions found</td></tr>`;
}

/* ---------------- Network ---------------- */

let networkHistoryReady = false;

function updateNetwork(network) {
  document.getElementById("net-upload").textContent = network.upload_speed;
  document.getElementById("net-download").textContent = network.download_speed;
  document.getElementById("net-sent").textContent = network.bytes_sent;
  document.getElementById("net-recv").textContent = network.bytes_received;
  document.getElementById("net-chart-value").textContent = `↑ ${network.upload_speed} / ↓ ${network.download_speed}`;

  const uploadKBs = (network.upload_speed_bps || 0) / 1024;
  const downloadKBs = (network.download_speed_bps || 0) / 1024;
  updateNetworkChart(charts.networkChart, uploadKBs.toFixed(1), downloadKBs.toFixed(1));

  const tbody = document.getElementById("interfaces-table-body");
  tbody.innerHTML = (network.interfaces || [])
    .map(
      (i) => `
      <tr>
        <td>${i.name}</td>
        <td>${i.ip}</td>
        <td><span class="pill-status ${i.is_up ? "badge-healthy" : "badge-critical"}">${i.is_up ? "up" : "down"}</span></td>
      </tr>`
    )
    .join("");
}

/* ---------------- Docker ---------------- */

function updateDocker(docker) {
  document.getElementById("docker-running").textContent = docker.running_containers ?? 0;
  document.getElementById("docker-stopped").textContent = docker.stopped_containers ?? 0;
  document.getElementById("docker-images").textContent = docker.images_count ?? 0;
  document.getElementById("docker-volumes").textContent = docker.volumes_count ?? 0;
  document.getElementById("docker-version-badge").textContent = docker.version ? `version ${docker.version}` : "unavailable";

  const tbody = document.getElementById("docker-table-body");
  const emptyState = document.getElementById("docker-empty-state");

  if (docker.available && docker.containers && docker.containers.length) {
    emptyState.classList.add("d-none");
    tbody.innerHTML = docker.containers
      .map(
        (c) => `
        <tr>
          <td>${c.id}</td>
          <td>${c.name}</td>
          <td>${c.image}</td>
          <td><span class="pill-status ${c.status === "running" ? "badge-healthy" : "badge-warning"}">${c.status}</span></td>
        </tr>`
      )
      .join("");
  } else {
    tbody.innerHTML = "";
    emptyState.classList.toggle("d-none", docker.available === true);
  }

  if (lastDockerAvailable === false && docker.available === true) {
    showToast("Docker daemon connected", "healthy");
  }
  lastDockerAvailable = docker.available;
}

/* ---------------- Processes ---------------- */

let currentSearchTerm = "";

function updateProcesses(processes) {
  const tbody = document.getElementById("process-table-body");
  const filtered = currentSearchTerm
    ? processes.filter((p) => p.name.toLowerCase().includes(currentSearchTerm))
    : processes;

  tbody.innerHTML = filtered
    .map(
      (p) => `
      <tr>
        <td>${p.pid}</td>
        <td>${p.name}</td>
        <td>${p.username}</td>
        <td>${p.cpu_percent}%</td>
        <td>${p.memory_percent}%</td>
        <td><span class="pill-status badge-healthy">${p.status}</span></td>
      </tr>`
    )
    .join("") || `<tr><td colspan="6" class="text-center text-muted">No matching processes</td></tr>`;
}

function setupProcessSearch() {
  const input = document.getElementById("process-search");
  input.addEventListener("input", (e) => {
    currentSearchTerm = e.target.value.trim().toLowerCase();
    fetchJSON(`/api/processes?search=${encodeURIComponent(currentSearchTerm)}`).then(
      (data) => data && updateProcesses(data.processes)
    );
  });
}

/* ---------------- System info ---------------- */

function updateSystemInfo(system) {
  const fields = [
    ["Hostname", system.hostname], ["Local IP", system.local_ip], ["Public IP", system.public_ip],
    ["OS", system.os], ["Kernel Version", system.kernel_version], ["Architecture", system.architecture],
    ["Logged-in User", system.logged_in_user], ["Uptime", system.uptime], ["Boot Time", system.boot_time],
    ["Python Version", system.python_version],
  ];
  document.getElementById("system-info-grid").innerHTML = `
    <div class="info-grid">
      ${fields.map(([label, val]) => `
        <div class="info-item">
          <span class="metric-label">${label}</span>
          <span class="metric-val">${val ?? "N/A"}</span>
        </div>`).join("")}
    </div>`;

  const tbody = document.getElementById("users-table-body");
  tbody.innerHTML = (system.logged_in_users || [])
    .map((u) => `<tr><td>${u.name}</td><td>${u.terminal}</td><td>${u.host}</td><td>${u.started}</td></tr>`)
    .join("") || `<tr><td colspan="4" class="text-center text-muted">No active sessions detected</td></tr>`;
}

/* ---------------- Helpers ---------------- */

function progressClass(value, warnAt, critAt, asStatus = false) {
  if (value >= critAt) return asStatus ? "critical" : "critical";
  if (value >= warnAt) return asStatus ? "warning" : "warning";
  return asStatus ? "healthy" : "";
}

function setupNav() {
  const links = document.querySelectorAll(".nav-link");
  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      links.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      document.getElementById(link.dataset.target).scrollIntoView({ behavior: "smooth" });
      document.getElementById("sidebar").classList.remove("open");
    });
  });
}

function setupThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  btn.addEventListener("click", () => {
    const body = document.body;
    const isDark = body.getAttribute("data-theme") === "dark";
    body.setAttribute("data-theme", isDark ? "light" : "dark");
    btn.innerHTML = isDark ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-stars-fill"></i>';
  });
}

function setupSidebarToggle() {
  const toggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
}

function setupExportButtons() {
  document.getElementById("export-pdf").addEventListener("click", () => {
    window.location.href = "/api/report/pdf";
    showToast("Generating PDF report...", "healthy");
  });

  document.getElementById("download-logs").addEventListener("click", async () => {
    const [summary, system] = await Promise.all([fetchJSON("/api/summary"), fetchJSON("/api/system")]);
    const content = `DevOps Health Dashboard — Snapshot Log\nGenerated: ${new Date().toISOString()}\n\n` +
      `SUMMARY\n${JSON.stringify(summary, null, 2)}\n\nSYSTEM\n${JSON.stringify(system, null, 2)}\n`;
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `dashboard-log-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Log snapshot downloaded", "healthy");
  });
}

function showToast(message, status = "healthy") {
  const colors = { healthy: "#34d399", warning: "#fbbf24", critical: "#f87171" };
  const container = document.getElementById("toast-container");
  const toastEl = document.createElement("div");
  toastEl.className = "toast align-items-center show mb-2";
  toastEl.setAttribute("role", "alert");
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body" style="border-left:3px solid ${colors[status] || colors.healthy}">
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 5000);
}
