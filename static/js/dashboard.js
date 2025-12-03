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

  // 현재 대시보드 view 가져오기 (electric, mechanical, instrument, meter 등)
  const viewScript = document.getElementById("dashboard-view");
  let currentView = "";
  try {
    currentView = viewScript ? JSON.parse(viewScript.textContent || '""') : "";
  } catch (error) {
    console.warn("Failed to parse dashboard view", error);
  }

  if (typeof Chart === "undefined") {
    console.error("Chart.js is not loaded");
    return;
  }

  // Register the plugin if it exists
  if (typeof ChartDataLabels !== 'undefined') {
    Chart.register(ChartDataLabels);
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          usePointStyle: true,
          pointStyle: 'line'
        }
      },
      tooltip: { mode: "index", intersect: false },
      datalabels: { display: false }, // 기본적으로 다른 차트에서는 숨김
    },
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: { grid: { display: false } },
      y: { beginAtZero: true, ticks: { precision: 0 } },
    },
  };

  const charts = {};

  const buildChart = (id, config) => {
    const canvas = document.getElementById(id);
    if (!canvas) {
      console.warn(`Canvas not found: ${id}`);
      return;
    }

    const context = canvas.getContext("2d");
    if (!context) {
      console.warn(`Context not found for: ${id}`);
      return;
    }

    const data = payload[config.dataKey];
    if (!data) {
      console.warn(`Data not found for key: ${config.dataKey}`);
      return;
    }

    charts[id] = new Chart(context, {
      type: config.type,
      data,
      options: config.options,
    });

    console.log(`Chart created: ${id}`);
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 1,
    plugins: {
      legend: { position: "right" },
      datalabels: {
        display: true,
        color: '#fff',
        font: {
          weight: 'bold',
          size: 11
        },
        formatter: (value, ctx) => {
          const label = ctx.chart.data.labels[ctx.dataIndex];
          const total = ctx.dataset.data.reduce((acc, curr) => acc + curr, 0);
          const percentage = ((value / total) * 100).toFixed(1) + "%";
          return `${label}\n${value}건\n${percentage}`;
        },
        textAlign: 'center'
      }
    },
  };

  const chartConfigs = [
    { id: "trendChart", type: "line", dataKey: "trend", options: chartOptions },
    { id: "damageChart", type: "bar", dataKey: "damage_trend", options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        datalabels: { display: false }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }},
    {
      id: "costCenterPie",
      type: "pie",
      dataKey: "cost_center_pie",
      options: pieOptions,
    },
    {
      id: "workctrPie",
      type: "doughnut",
      dataKey: "workctr_pie",
      options: pieOptions,
    },
    { id: "costChart", type: "bar", dataKey: "cost_chart", options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        datalabels: { display: false }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true }
      }
    }},
    {
      id: "workctrTime",
      type: "bar",
      dataKey: "workctr_time",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          datalabels: { display: false }
        },
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
        plugins: { legend: { position: "top" }, datalabels: { display: false } },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: {
            stacked: true,
            beginAtZero: true,
            title: { display: true, text: "건수" },
            ticks: { precision: 0 }
          }
        },
      },
    },
    {
      id: "statusCost",
      type: "bar",
      dataKey: "status_by_cost",
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "top" }, datalabels: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { beginAtZero: true, ticks: { precision: 0 } }
        },
      },
    },
  ];

  chartConfigs.forEach((config) => buildChart(config.id, config));

  // 직영/상주 비교 도넛 차트 초기화 (작업반 대시보드에서만)
  const comparisonDonutOptions = {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 1,
    plugins: {
      legend: { position: "bottom" },
      datalabels: {
        display: true,
        color: '#fff',
        font: {
          weight: 'bold',
          size: 12
        },
        formatter: (value, ctx) => {
          const label = ctx.chart.data.labels[ctx.dataIndex];
          const total = ctx.dataset.data.reduce((acc, curr) => acc + curr, 0);
          const percentage = ((value / total) * 100).toFixed(1) + "%";
          // Order 차트는 건수, Work 차트는 시간
          const unit = ctx.chart.canvas.id.includes("Order") ? "건" : "h";
          return `${label}\n${value}${unit}\n${percentage}`;
        },
        textAlign: 'center'
      }
    },
  };

  // 직영/상주 비교 차트 초기화
  if (payload.workctr_comparison) {
    const orderCanvas = document.getElementById("workctrComparisonOrder");
    const workCanvas = document.getElementById("workctrComparisonWork");

    if (orderCanvas && payload.workctr_comparison.order_count) {
      charts["workctrComparisonOrder"] = new Chart(orderCanvas.getContext("2d"), {
        type: "doughnut",
        data: payload.workctr_comparison.order_count,
        options: comparisonDonutOptions,
      });
      console.log("Chart created: workctrComparisonOrder");
    }

    if (workCanvas && payload.workctr_comparison.actual_work) {
      charts["workctrComparisonWork"] = new Chart(workCanvas.getContext("2d"), {
        type: "doughnut",
        data: payload.workctr_comparison.actual_work,
        options: comparisonDonutOptions,
      });
      console.log("Chart created: workctrComparisonWork");
    }
  }

  // 호기별 정비비용 차트 초기화
  if (payload.cost_by_center) {
    const costByCenterCanvas = document.getElementById("costByCenter");
    if (costByCenterCanvas) {
      charts["costByCenter"] = new Chart(costByCenterCanvas.getContext("2d"), {
        type: "bar",
        data: payload.cost_by_center,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top" },
            datalabels: { display: false }
          },
          scales: {
            x: { grid: { display: false } },
            y: { beginAtZero: true }
          }
        },
      });
      console.log("Chart created: costByCenter");
    }
  }

  console.log("Charts initialized");
  console.log("Payload keys:", Object.keys(payload));

  // 개별 차트 필터링 기능 초기화
  if (payload.filter_options) {
    console.log("Initializing chart filters");
    initChartFilters();
  } else {
    console.warn("Filter options not available");
  }

  function initChartFilters() {
    const options = payload.filter_options;
    if (!options) return;

    const currentYear = new Date().getFullYear().toString();

    // 모든 차트 컨트롤 초기화
    document.querySelectorAll(".chart-controls").forEach(control => {
      const startYearSelect = control.querySelector(".chart-start-year");
      const startMonthSelect = control.querySelector(".chart-start-month");
      const endYearSelect = control.querySelector(".chart-end-year");
      const endMonthSelect = control.querySelector(".chart-end-month");

      // 차트 ID 가져오기 (어느 셀렉트박스에서든 가져올 수 있음)
      const chartId = startYearSelect.dataset.chart;

      if (!startYearSelect || !startMonthSelect || !endYearSelect || !endMonthSelect) return;

      // 년도 옵션 추가
      options.years.forEach(year => {
        startYearSelect.add(new Option(year + "년", year));
        endYearSelect.add(new Option(year + "년", year));
      });

      // 월 옵션 추가
      options.months.forEach(month => {
        startMonthSelect.add(new Option(month + "월", month));
        endMonthSelect.add(new Option(month + "월", month));
      });

      // 초기값 설정: equipmentDamage는 2020년부터, 나머지는 올해
      if (chartId === "equipmentDamage") {
        startYearSelect.value = "2020";
      } else {
        startYearSelect.value = currentYear;
      }
      startMonthSelect.value = "01";
      endYearSelect.value = currentYear;
      endMonthSelect.value = "12";

      // 이벤트 리스너 추가
      [startYearSelect, startMonthSelect, endYearSelect, endMonthSelect].forEach(el => {
        el.addEventListener("change", () => fetchChartData(chartId));
      });
    });

    // 페이지 로드 시 존재하는 차트에만 올해 데이터로 필터 적용
    const chartIds = ["trendChart", "damageChart", "costCenterPie", "workctrPie", "costChart", "workctrTime", "equipmentDamage", "statusCost", "workctrComparison", "costByCenter"];
    chartIds.forEach(chartId => {
      // workctrComparison은 두 개의 캔버스를 사용하므로 별도 체크
      if (chartId === "workctrComparison") {
        if (document.getElementById("workctrComparisonOrder")) {
          fetchChartData(chartId);
        }
      } else if (document.getElementById(chartId)) {
        fetchChartData(chartId);
      }
    });

    // 비용 유형 셀렉트박스 이벤트 리스너 추가
    const costTypeSelect = document.querySelector('.chart-cost-type[data-chart="costByCenter"]');
    if (costTypeSelect) {
      costTypeSelect.addEventListener("change", () => fetchCostByCenterData());
    }

    // costChart 비용 유형 셀렉트박스 이벤트 리스너 추가
    const costChartTypeSelect = document.querySelector('.chart-cost-type[data-chart="costChart"]');
    if (costChartTypeSelect) {
      costChartTypeSelect.addEventListener("change", () => fetchCostChartData());
    }
  }

  function fetchChartData(chartId) {
    const startYearEl = document.querySelector(`.chart-start-year[data-chart="${chartId}"]`);
    if (!startYearEl) return; // 해당 차트가 DOM에 없으면 스킵

    const startYear = startYearEl.value;
    const startMonth = document.querySelector(`.chart-start-month[data-chart="${chartId}"]`).value;
    const endYear = document.querySelector(`.chart-end-year[data-chart="${chartId}"]`).value;
    const endMonth = document.querySelector(`.chart-end-month[data-chart="${chartId}"]`).value;

    const startYM = `${startYear}-${startMonth}`;
    const endYM = `${endYear}-${endMonth}`;

    if (startYM > endYM) {
      alert("시작일이 종료일보다 클 수 없습니다.");
      return;
    }

    // 차트 컨테이너에 로딩 표시 (선택사항)
    const chart = charts[chartId];
    if (chart) {
      chart.canvas.style.opacity = "0.5";
    }

    fetch("/dashboard/api/filter-chart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chart_id: chartId,
        start_ym: startYM,
        end_ym: endYM,
        view: currentView,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error("데이터 요청 실패");
        return response.json();
      })
      .then(data => {
        updateChart(chartId, data);
      })
      .catch(error => {
        console.error(`Error updating chart ${chartId}:`, error);
        alert("데이터를 불러오는 중 오류가 발생했습니다.");
      })
      .finally(() => {
        if (chart) {
          chart.canvas.style.opacity = "1";
        }
      });
  }

  function updateChart(chartId, data) {
    // workctrComparison은 두 개의 차트를 업데이트
    if (chartId === "workctrComparison") {
      const orderChart = charts["workctrComparisonOrder"];
      const workChart = charts["workctrComparisonWork"];

      if (orderChart && data.order_count) {
        orderChart.data.labels = data.order_count.labels;
        orderChart.data.datasets = data.order_count.datasets;
        orderChart.update();
      }

      if (workChart && data.actual_work) {
        workChart.data.labels = data.actual_work.labels;
        workChart.data.datasets = data.actual_work.datasets;
        workChart.update();
      }
      return;
    }

    const chart = charts[chartId];
    if (chart && data) {
      chart.data.labels = data.labels;
      chart.data.datasets = data.datasets;
      chart.update();
    }
  }

  // Equipment 검색 필터 초기화
  const equipmentSearchInput = document.getElementById("equipmentSearch");
  if (equipmentSearchInput) {
    let searchTimeout;
    equipmentSearchInput.addEventListener("input", () => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        fetchEquipmentDamageData();
      }, 500); // 500ms 디바운스
    });
  }

  function fetchEquipmentDamageData() {
    const equipmentSearch = document.getElementById("equipmentSearch")?.value || "";
    const startYear = document.querySelector('.chart-start-year[data-chart="equipmentDamage"]')?.value;
    const startMonth = document.querySelector('.chart-start-month[data-chart="equipmentDamage"]')?.value;
    const endYear = document.querySelector('.chart-end-year[data-chart="equipmentDamage"]')?.value;
    const endMonth = document.querySelector('.chart-end-month[data-chart="equipmentDamage"]')?.value;

    if (!startYear || !startMonth || !endYear || !endMonth) return;

    const startYM = `${startYear}-${startMonth}`;
    const endYM = `${endYear}-${endMonth}`;

    if (startYM > endYM) {
      alert("시작일이 종료일보다 클 수 없습니다.");
      return;
    }

    const chart = charts["equipmentDamage"];
    if (chart) {
      chart.canvas.style.opacity = "0.5";
    }

    fetch("/dashboard/api/filter-equipment-damage", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        equipment: equipmentSearch,
        start_ym: startYM,
        end_ym: endYM,
        view: currentView,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error("데이터 요청 실패");
        return response.json();
      })
      .then(data => {
        updateChart("equipmentDamage", data);
      })
      .catch(error => {
        console.error("Error updating equipment damage chart:", error);
      })
      .finally(() => {
        if (chart) {
          chart.canvas.style.opacity = "1";
        }
      });
  }

  // 호기별 정비비용 데이터 fetch 함수
  function fetchCostByCenterData() {
    const costType = document.querySelector('.chart-cost-type[data-chart="costByCenter"]')?.value || "Total Cost";
    const startYear = document.querySelector('.chart-start-year[data-chart="costByCenter"]')?.value;
    const startMonth = document.querySelector('.chart-start-month[data-chart="costByCenter"]')?.value;
    const endYear = document.querySelector('.chart-end-year[data-chart="costByCenter"]')?.value;
    const endMonth = document.querySelector('.chart-end-month[data-chart="costByCenter"]')?.value;

    if (!startYear || !startMonth || !endYear || !endMonth) return;

    const startYM = `${startYear}-${startMonth}`;
    const endYM = `${endYear}-${endMonth}`;

    if (startYM > endYM) {
      alert("시작일이 종료일보다 클 수 없습니다.");
      return;
    }

    const chart = charts["costByCenter"];
    if (chart) {
      chart.canvas.style.opacity = "0.5";
    }

    fetch("/dashboard/api/filter-chart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chart_id: "costByCenter",
        cost_type: costType,
        start_ym: startYM,
        end_ym: endYM,
        view: currentView,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error("데이터 요청 실패");
        return response.json();
      })
      .then(data => {
        updateChart("costByCenter", data);
      })
      .catch(error => {
        console.error("Error updating cost by center chart:", error);
      })
      .finally(() => {
        if (chart) {
          chart.canvas.style.opacity = "1";
        }
      });
  }

  // 월별 비용 추이 데이터 fetch 함수
  function fetchCostChartData() {
    const costType = document.querySelector('.chart-cost-type[data-chart="costChart"]')?.value || "Total Cost";
    const startYear = document.querySelector('.chart-start-year[data-chart="costChart"]')?.value;
    const startMonth = document.querySelector('.chart-start-month[data-chart="costChart"]')?.value;
    const endYear = document.querySelector('.chart-end-year[data-chart="costChart"]')?.value;
    const endMonth = document.querySelector('.chart-end-month[data-chart="costChart"]')?.value;

    if (!startYear || !startMonth || !endYear || !endMonth) return;

    const startYM = `${startYear}-${startMonth}`;
    const endYM = `${endYear}-${endMonth}`;

    if (startYM > endYM) {
      alert("시작일이 종료일보다 클 수 없습니다.");
      return;
    }

    const chart = charts["costChart"];
    if (chart) {
      chart.canvas.style.opacity = "0.5";
    }

    fetch("/dashboard/api/filter-chart", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        chart_id: "costChart",
        cost_type: costType,
        start_ym: startYM,
        end_ym: endYM,
        view: currentView,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error("데이터 요청 실패");
        return response.json();
      })
      .then(data => {
        updateChart("costChart", data);
      })
      .catch(error => {
        console.error("Error updating cost chart:", error);
      })
      .finally(() => {
        if (chart) {
          chart.canvas.style.opacity = "1";
        }
      });
  }

  // equipmentDamage, costByCenter, costChart 차트의 날짜 필터 변경 시 전용 함수 사용
  const originalFetchChartData = fetchChartData;
  fetchChartData = function(chartId) {
    if (chartId === "equipmentDamage") {
      fetchEquipmentDamageData();
    } else if (chartId === "costByCenter") {
      fetchCostByCenterData();
    } else if (chartId === "costChart") {
      fetchCostChartData();
    } else {
      originalFetchChartData(chartId);
    }
  };
});
