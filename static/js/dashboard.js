document.addEventListener("DOMContentLoaded", () => {
  const dataScript = document.getElementById("dashboard-data");
  if (!dataScript) return;

  let payload;
  try {
    payload = JSON.parse(dataScript.textContent || "{}");
  } catch (error) {
    console.error("Failed to parse dashboard payload", error);
    return;
  }

  if (typeof Chart === "undefined") {
    console.error("Chart.js is not loaded");
    return;
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" },
      tooltip: { mode: "index", intersect: false },
    },
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: { grid: { display: false } },
      y: { beginAtZero: true, ticks: { precision: 0 } },
    },
  };

  const buildChart = (id, config) => {
    const canvas = document.getElementById(id);
    if (!canvas) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const data = payload[config.dataKey];
    if (!data) return;

    new Chart(context, {
      type: config.type,
      data,
      options: config.options,
    });
  };

  const chartConfigs = [
    { id: "trendChart", type: "line", dataKey: "trend", options: chartOptions },
    { id: "damageChart", type: "line", dataKey: "damage_trend", options: chartOptions },
    {
      id: "costCenterPie",
      type: "pie",
      dataKey: "cost_center_pie",
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: { legend: { position: "right" } },
      },
    },
    {
      id: "workctrPie",
      type: "doughnut",
      dataKey: "workctr_pie",
      options: {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1,
        plugins: { legend: { position: "right" } },
      },
    },
    { id: "costChart", type: "line", dataKey: "cost_chart", options: chartOptions },
    {
      id: "workctrTime",
      type: "bar",
      dataKey: "workctr_time",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    },
    {
      id: "equipmentDamage",
      type: "bar",
      dataKey: "equipment_damage",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
      },
    },
    {
      id: "statusCost",
      type: "bar",
      dataKey: "status_by_cost",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" } },
        scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } },
      },
    },
  ];

  chartConfigs.forEach((config) => buildChart(config.id, config));
});
