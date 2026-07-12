/**
 * charts.js
 * Initializes and updates the four live Chart.js line/bar charts:
 * CPU, RAM, Disk (gauges as rolling line charts) and Network (dual-line).
 */

const MAX_POINTS = 30;

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio:2,
  animation: { duration: 400, easing: "easeOutQuart" },
  interaction: { intersect: false, mode: "index" },
  plugins: { legend: { display: false } },
  scales: {
    x: { display: false },
    y: {
      beginAtZero: true,
      max: 100,
      grid: { color: "rgba(148,163,184,0.08)" },
      ticks: { color: "#8b97b0", font: { family: "JetBrains Mono", size: 10 } },
    },
  },
};

function makeLineDataset(label, color) {
  return {
    label,
    data: [],
    borderColor: color,
    backgroundColor: (ctx) => {
      const gradient = ctx.chart.ctx.createLinearGradient(0, 0, 0, 160);
      gradient.addColorStop(0, color + "33");
      gradient.addColorStop(1, color + "00");
      return gradient;
    },
    fill: true,
    tension: 0.35,
    borderWidth: 2,
    pointRadius: 0,
  };
}

function initCharts() {
  const labels = Array(MAX_POINTS).fill("");

  const cpuChart = new Chart(document.getElementById("cpuChart"), {
    type: "line",
    data: { labels, datasets: [makeLineDataset("CPU %", "#22d3ee")] },
    options: chartDefaults,
  });

  const ramChart = new Chart(document.getElementById("ramChart"), {
    type: "line",
    data: { labels, datasets: [makeLineDataset("RAM %", "#818cf8")] },
    options: chartDefaults,
  });

  const diskChart = new Chart(document.getElementById("diskChart"), {
    type: "line",
    data: { labels, datasets: [makeLineDataset("Disk %", "#fbbf24")] },
    options: chartDefaults,
  });

  const networkChart = new Chart(document.getElementById("networkChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        makeLineDataset("Upload (KB/s)", "#34d399"),
        makeLineDataset("Download (KB/s)", "#f87171"),
      ],
    },
    options: {
      ...chartDefaults,
      scales: {
        x: { display: false },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(148,163,184,0.08)" },
          ticks: { color: "#8b97b0", font: { family: "JetBrains Mono", size: 10 } },
        },
      },
      plugins: { legend: { display: true, labels: { color: "#8b97b0", boxWidth: 10, font: { size: 10 } } } },
    },
  });

  return { cpuChart, ramChart, diskChart, networkChart };
}

function pushPoint(chart, datasetIndex, value) {
  const dataset = chart.data.datasets[datasetIndex];
  dataset.data.push(value);
  if (dataset.data.length > MAX_POINTS) dataset.data.shift();
  chart.data.labels.push("");
  if (chart.data.labels.length > MAX_POINTS) chart.data.labels.shift();
}

function updateSingleChart(chart, value) {
  pushPoint(chart, 0, value);
  chart.update("none");
}

function updateNetworkChart(chart, uploadKBs, downloadKBs) {
  pushPoint(chart, 0, uploadKBs);
  chart.data.datasets[1].data.push(downloadKBs);
  if (chart.data.datasets[1].data.length > MAX_POINTS) chart.data.datasets[1].data.shift();
  chart.update("none");
}
