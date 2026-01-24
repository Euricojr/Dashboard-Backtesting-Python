// FinSense Engine Script
// Refactored for Dark/Neon Design System

let mainChart;
let candleSeries;
let perfChart;
let strategySeries;
let assetSeries;
let allAssets = {};

// Colors from VECTRA System
const COLORS = {
  bg: "#121214",
  text: "#f4f4f5",
  secondary: "#a1a1aa",
  border: "#27272a",
  neonGreen: "#00E396",
  neonRed: "#FF4560",
  accent: "#7E57C2",
};

// --- INICIALIZAÇÃO ---

async function loadAssets() {
  try {
    const res = await fetch("/assets");
    allAssets = await res.json();

    const trigger = document.getElementById("sidebar_trigger");
    const modal = document.getElementById("search_modal");
    const searchInput = document.getElementById("modal_search_input");

    const openModal = () => {
      modal.style.display = "flex";
      searchInput.value = "";
      renderModalResults("");
      setTimeout(() => searchInput.focus(), 100);
    };

    const closeModal = () => {
      modal.style.display = "none";
    };

    trigger.addEventListener("click", openModal);

    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        openModal();
      }
      if (e.key === "Escape") closeModal();
    });

    modal.addEventListener("click", (e) => {
      if (e.target === modal) closeModal();
    });

    searchInput.addEventListener("input", (e) =>
      renderModalResults(e.target.value),
    );
  } catch (err) {
    console.error("Erro ao carregar ativos:", err);
  }
}

function renderModalResults(query) {
  const resultsDiv = document.getElementById("modal_results");
  const q = query.toLowerCase();
  resultsDiv.innerHTML = "";

  let hasResults = false;

  for (const [category, stocks] of Object.entries(allAssets)) {
    const filtered = Object.entries(stocks).filter(
      ([ticker, name]) =>
        ticker.toLowerCase().includes(q) || name.toLowerCase().includes(q),
    );

    if (filtered.length > 0) {
      hasResults = true;
      const group = document.createElement("div");
      group.className =
        "search-modal-group p-3 text-secondary small fw-bold text-uppercase";
      group.style.background = "rgba(255,255,255,0.02)";
      group.innerText = category;
      resultsDiv.appendChild(group);

      filtered.forEach(([ticker, name]) => {
        const item = document.createElement("div");
        item.className =
          "list-group-item-dark p-3 d-flex justify-content-between align-items-center border-bottom border-secondary-subtle";
        item.innerHTML = `
                    <div class="d-flex flex-column">
                        <span class="fw-bold text-white">${name}</span>
                        <span class="text-secondary small">${category}</span>
                    </div>
                    <span class="badge bg-green-lt">${ticker}</span>
                `;
        item.onclick = () => selectAsset(ticker, name);
        resultsDiv.appendChild(item);
      });
    }
  }

  if (!hasResults && q !== "") {
    const none = document.createElement("div");
    none.className = "p-5 text-center text-muted";
    none.innerText = 'Nenhum ativo encontrado para "' + query + '"';
    resultsDiv.appendChild(none);
  }
}

function selectAsset(ticker, name) {
  const label = document.getElementById("trigger_label");
  const hidden = document.getElementById("selected_ticker");
  const modal = document.getElementById("search_modal");

  // New Display Elements
  const displayTicker = document.getElementById("display_ticker");
  const displayName = document.getElementById("display_name");
  const logoImg = document.getElementById("asset_logo");
  const logoPlaceholder = document.getElementById("asset_icon_placeholder");

  label.innerText = name;
  hidden.value = ticker;
  modal.style.display = "none";

  // Update Premium Display
  if (displayTicker) displayTicker.innerText = ticker.split(".")[0];
  if (displayName) displayName.innerText = name;

  // Logo Logic
  if (logoImg) {
    const cleanTicker = ticker.split(".")[0];
    logoImg.src = `https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/${cleanTicker}.png`;
    logoImg.onload = () => {
      logoImg.style.display = "block";
      logoPlaceholder.style.display = "none";
    };
    logoImg.onerror = () => {
      logoImg.style.display = "none";
      logoPlaceholder.style.display = "block";
    };
  }
}

function initChart() {
  const chartElement = document.getElementById("chart");
  const perfElement = document.getElementById("perf_chart");

  if (!chartElement) return;

  const commonOptions = {
    layout: {
      background: { type: "solid", color: COLORS.bg },
      textColor: COLORS.text,
      fontSize: 12,
      fontFamily: "Inter, sans-serif",
    },
    grid: {
      vertLines: { color: "rgba(42, 46, 57, 0.15)" },
      horzLines: { color: "rgba(42, 46, 57, 0.15)" },
    },
    rightPriceScale: { borderColor: COLORS.border },
    timeScale: { borderColor: COLORS.border, timeVisible: true },
    crosshair: { mode: 1 },
  };

  mainChart = LightweightCharts.createChart(chartElement, commonOptions);

  candleSeries = mainChart.addCandlestickSeries({
    upColor: COLORS.neonGreen,
    downColor: COLORS.neonRed,
    borderVisible: false,
    wickUpColor: COLORS.neonGreen,
    wickDownColor: COLORS.neonRed,
  });

  window.smaShortSeries = mainChart.addLineSeries({
    color: "#FFEB3B",
    lineWidth: 2,
    title: "SMA Curta",
  });
  window.smaLongSeries = mainChart.addLineSeries({
    color: "#E040FB",
    lineWidth: 2,
    title: "SMA Longa",
  });

  window.vLineSeries = mainChart.addHistogramSeries({
    color: "rgba(255, 215, 0, 0.3)",
    lastValueVisible: false,
    priceScaleId: "split_scale",
  });
  mainChart
    .priceScale("split_scale")
    .applyOptions({ visible: false, autoScale: true });

  mainChart.priceScale("left").applyOptions({ visible: false });

  perfChart = LightweightCharts.createChart(perfElement, commonOptions);
  strategySeries = perfChart.addLineSeries({
    color: COLORS.neonGreen,
    lineWidth: 3,
    title: "Estratégia",
  });
  assetSeries = perfChart.addLineSeries({
    color: COLORS.secondary,
    lineWidth: 2,
    lineStyle: 2,
    title: "Buy & Hold",
  });

  window.rsiSeries = mainChart.addLineSeries({
    color: COLORS.accent,
    lineWidth: 2,
    priceScaleId: "left",
    title: "RSI (14)",
  });

  const handleResize = () => {
    mainChart.resize(chartElement.clientWidth, chartElement.clientHeight);
    perfChart.resize(perfElement.clientWidth, perfElement.clientHeight);
  };
  window.addEventListener("resize", handleResize);
  setTimeout(handleResize, 500);
}

function renderMetrics(data) {
  const m = data.metrics;
  const t = data.trade_stats;
  const grid = document.getElementById("metrics-grid");

  if (!grid) return;

  const createCard = (label, value, icon, type = "neutral") => {
    let valClass = "val-neu";
    let accentClass = "accent-purple";
    let displayVal = value;

    if (type === "pct") {
      displayVal = value;
      const numeric = parseFloat(value.replace("%", ""));
      if (numeric > 0) {
        valClass = "val-pos";
        accentClass = "accent-green";
      } else if (numeric < 0) {
        valClass = "val-neg";
        accentClass = "accent-red";
      }
    } else if (type === "drawdown") {
      displayVal = value;
      valClass = "val-neg";
      accentClass = "accent-red";
    } else if (type === "pf") {
      displayVal = value.toFixed(2);
      if (value >= 1.5) {
        valClass = "val-pos";
        accentClass = "accent-green";
      } else if (value >= 1.0) {
        valClass = "val-warn";
        accentClass = "accent-warn";
      } else {
        valClass = "val-neg";
        accentClass = "accent-red";
      }
    } else if (type === "winrate") {
      displayVal = (value * 100).toFixed(2) + "%";
      valClass = value > 0.5 ? "val-pos" : "val-warn";
      accentClass = value > 0.5 ? "accent-green" : "accent-warn";
    } else if (type === "int") {
      displayVal = value;
      accentClass = "accent-blue";
    }

    return `
            <div class="metric-card ${accentClass}">
                <span class="metric-label"><i class="${icon}"></i>${label}</span>
                <span class="metric-value ${valClass}">${displayVal}</span>
            </div>
        `;
  };

  grid.innerHTML = `
        ${createCard("Retorno Total", m.total_return, "ri-funds-box-line", "pct")}
        ${createCard("Win Rate", t.win_rate, "ri-crosshair-2-line", "winrate")}
        ${createCard("Profit Factor", t.profit_factor, "ri-scales-3-line", "pf")}
        ${createCard("Total Trades", t.total_trades, "ri-exchange-dollar-line", "int")}
        
        ${createCard("Max Drawdown", m.max_drawdown, "ri-arrow-down-circle-line", "drawdown")}
        ${createCard("Sharpe Ratio", m.sharpe_ratio, "ri-pulse-line", "neutral")}
        ${createCard("Volatilidade", m.volatilidade_anual, "ri-activity-line", "pct")}
        ${createCard("CAGR Anual", m.cagr, "ri-stock-line", "pct")}
    `;
}

async function runBacktest() {
  const ticker = document.getElementById("selected_ticker").value;
  const start = document.getElementById("start_date").value;
  const end = document.getElementById("end_date").value;
  const strategy = document.getElementById("strategy_select").value;
  const smaShort = document.getElementById("sma_short").value;
  const smaLong = document.getElementById("sma_long").value;
  const btn = document.getElementById("run_btn");
  const spinner = document.getElementById("chart_spinner");
  const placeholder = document.getElementById("chart_placeholder");

  btn.disabled = true;
  btn.innerHTML =
    '<i class="ri-loader-4-line ri-spin-2 me-2"></i>PROCESSANDO...';
  spinner.style.display = "block";

  try {
    const response = await fetch("/run_backtest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ticker,
        start,
        end,
        strategy,
        sma_short: smaShort,
        sma_long: smaLong,
      }),
    });

    const data = await response.json();
    if (data.error) {
      alert("Erro: " + data.error);
      return;
    }

    placeholder.style.display = "none";
    candleSeries.setData(data.candle_data);

    if (data.sma_short_data) window.smaShortSeries.setData(data.sma_short_data);
    if (data.sma_long_data) window.smaLongSeries.setData(data.sma_long_data);

    candleSeries.setMarkers(data.markers);
    mainChart.timeScale().fitContent();

    if (data.equity_data) {
      strategySeries.setData(
        data.equity_data.map((d) => ({ time: d.time, value: d.strategy })),
      );
      assetSeries.setData(
        data.equity_data.map((d) => ({ time: d.time, value: d.asset })),
      );
      perfChart.timeScale().fitContent();
    }

    renderMetrics(data);

    const aiBox = document.getElementById("ai_analysis");
    if (aiBox) {
      aiBox.innerHTML = data.ai_analysis;
      aiBox.style.borderLeft = `4px solid ${data.is_warning ? COLORS.neonRed : COLORS.neonGreen}`;
      aiBox.classList.add("p-3", "rounded");
      aiBox.style.background = "rgba(255,255,255,0.03)";
    }

    document.getElementById("results_area").style.display = "flex";
  } catch (err) {
    console.error(err);
    alert("Falha de conexão com o terminal FinSense!");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="ri-play-fill me-2"></i>EXECUTAR BACKTEST';
    spinner.style.display = "none";

    setTimeout(() => {
      const chartDiv = document.getElementById("chart");
      const perfDiv = document.getElementById("perf_chart");
      if (chartDiv) mainChart.resize(chartDiv.clientWidth, 500);
      if (perfDiv) {
        perfChart.resize(perfDiv.clientWidth, 280);
        perfChart.timeScale().fitContent();
      }
    }, 300);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initChart();
  loadAssets();
  document.getElementById("run_btn").addEventListener("click", runBacktest);

  const strategySelect = document.getElementById("strategy_select");
  const smaSettings = document.getElementById("sma_settings");

  strategySelect.addEventListener("change", () => {
    smaSettings.style.display =
      strategySelect.value === "SMA" ? "block" : "none";
  });

  initBatchFeature();
});

async function initBatchFeature() {
  const btn = document.getElementById("btn_run_batch");
  const select = document.getElementById("batch_category");

  setTimeout(() => {
    select.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "ALL";
    optAll.innerText = "⭐ Todas as Categorias";
    select.appendChild(optAll);

    for (const cat of Object.keys(allAssets)) {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.innerText = cat;
      select.appendChild(opt);
    }
  }, 1500);

  btn.addEventListener("click", async () => {
    const loading = document.getElementById("batch_loading");
    const resultsArea = document.getElementById("batch_results_area");
    const tableBody = document.getElementById("batch_table_body");

    loading.style.display = "block";
    resultsArea.style.display = "none";
    btn.disabled = true;

    const start = document.getElementById("start_date").value;
    const end = document.getElementById("end_date").value;
    const strategy = document.getElementById("strategy_select").value;
    const smaShort = document.getElementById("sma_short").value;
    const smaLong = document.getElementById("sma_long").value;
    const cate = select.value;

    try {
      const res = await fetch("/batch_backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: cate,
          start,
          end,
          strategy,
          sma_short: smaShort,
          sma_long: smaLong,
        }),
      });

      const data = await res.json();
      tableBody.innerHTML = "";

      data.forEach((item, index) => {
        const tr = document.createElement("tr");
        const isPositive = item.return_out > 0;

        tr.innerHTML = `
                    <td><span class="badge ${index < 3 ? "bg-yellow text-dark" : "bg-dark text-secondary"}">#${index + 1}</span></td>
                    <td class="fw-bold">${item.ticker}</td>
                    <td class="text-secondary small">${item.name}</td>
                    <td class="text-end fw-bold ${isPositive ? "val-profit" : "val-loss"}">${(item.return_out * 100).toFixed(2)}%</td>
                    <td class="text-end fw-bold">${item.sharpe_out.toFixed(2)}</td>
                    <td class="text-end val-loss">${(item.drawdown_out * 100).toFixed(2)}%</td>
                    <td class="text-end">
                       <button class="btn btn-sm btn-neon-outline" onclick="loadFromBatch('${item.ticker}', '${item.name}')">Ver</button>
                    </td>
                `;
        tableBody.appendChild(tr);
      });

      loading.style.display = "none";
      resultsArea.style.display = "block";
    } catch (err) {
      console.error(err);
      alert("Erro ao executar varredura batch!");
      loading.style.display = "none";
    } finally {
      btn.disabled = false;
    }
  });
}

window.loadFromBatch = function (ticker, name) {
  // Global for onclick
  const modalEl = document.getElementById("modal_batch");
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();

  document.getElementById("selected_ticker").value = ticker;
  document.getElementById("trigger_label").innerText = name;

  runBacktest();
};
