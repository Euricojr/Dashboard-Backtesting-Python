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

  for (const [key, categoryData] of Object.entries(allAssets)) {
    const filtered = Object.entries(categoryData.data).filter(
      ([ticker, name]) =>
        ticker.toLowerCase().includes(q) || name.toLowerCase().includes(q),
    );

    if (filtered.length > 0) {
      hasResults = true;
      const group = document.createElement("div");
      group.className =
        "search-modal-group p-3 text-secondary small fw-bold text-uppercase";
      group.style.background = "rgba(255,255,255,0.02)";
      group.innerText = categoryData.label;
      resultsDiv.appendChild(group);

      filtered.forEach(([ticker, name]) => {
        const item = document.createElement("div");
        item.className =
          "list-group-item-dark p-3 d-flex justify-content-between align-items-center border-bottom border-secondary-subtle";
        item.innerHTML = `
                    <div class="d-flex flex-column">
                        <span class="fw-bold text-white">${name}</span>
                        <span class="text-secondary small">${categoryData.label}</span>
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

const ASSET_LOGOS = {
  AAPL: "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg",
  MSFT: "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
  NVDA: "https://upload.wikimedia.org/wikipedia/commons/a/a4/NVIDIA_logo.svg",
  GOOGL: "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
  AMZN: "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
  META: "https://upload.wikimedia.org/wikipedia/commons/0/05/Meta_Platforms_Logo.svg",
  TSLA: "https://upload.wikimedia.org/wikipedia/commons/b/bd/Tesla_Motors.svg",
  "BRK-B": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Berkshire_Hathaway_Logo.svg",
  LLY: "https://upload.wikimedia.org/wikipedia/commons/1/1f/Eli_Lilly_and_Company_logo.svg",
  AVGO: "https://upload.wikimedia.org/wikipedia/commons/1/1c/Broadcom_Logo.svg",
  WMT: "https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg",
  JPM: "https://upload.wikimedia.org/wikipedia/commons/6/6f/JPMorgan_Chase_logo.svg",
  V: "https://upload.wikimedia.org/wikipedia/commons/5/5e/Visa_Inc._logo.svg",
  ORCL: "https://upload.wikimedia.org/wikipedia/commons/5/50/Oracle_logo.svg",
  XOM: "https://upload.wikimedia.org/wikipedia/commons/8/8f/ExxonMobil_Logo.svg",
  MA: "https://upload.wikimedia.org/wikipedia/commons/a/a4/Mastercard_2019_logo.svg",
  JNJ: "https://upload.wikimedia.org/wikipedia/commons/3/3f/Johnson_and_Johnson_Logo.svg",
  NFLX: "https://upload.wikimedia.org/wikipedia/commons/7/7a/Netflix_logo.svg",
  BAC: "https://upload.wikimedia.org/wikipedia/commons/2/2d/Bank_of_America_logo.svg",
  ABBV: "https://upload.wikimedia.org/wikipedia/commons/1/1a/AbbVie_logo.svg",
  COST: "https://upload.wikimedia.org/wikipedia/commons/5/5f/Costco_Wholesale_logo.svg",
  PG: "https://upload.wikimedia.org/wikipedia/commons/8/85/Procter_%26_Gamble_logo.svg",
  HD: "https://upload.wikimedia.org/wikipedia/commons/5/5f/The_Home_Depot_logo.svg",
  AMD: "https://upload.wikimedia.org/wikipedia/commons/7/7c/AMD_Logo.svg",
  ADBE: "https://upload.wikimedia.org/wikipedia/commons/4/4c/Adobe_Corporate_Logo.png",
  CRM: "https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg",
  KO: "https://upload.wikimedia.org/wikipedia/commons/c/ce/Coca-Cola_logo.svg",
  PEP: "https://upload.wikimedia.org/wikipedia/commons/6/68/Pepsi_2023.svg",
  TMO: "https://upload.wikimedia.org/wikipedia/commons/7/7e/Thermo_Fisher_Scientific_logo.svg",
  DIS: "https://upload.wikimedia.org/wikipedia/commons/d/df/The_Walt_Disney_Company_logo.svg",
  CSCO: "https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg",
  INTU: "https://upload.wikimedia.org/wikipedia/commons/4/4e/Intuit_logo.svg",
  PFE: "https://upload.wikimedia.org/wikipedia/commons/8/8e/Pfizer_logo.svg",
  LIN: "https://upload.wikimedia.org/wikipedia/commons/6/6f/Linde_plc_logo.svg",
  AMAT: "https://upload.wikimedia.org/wikipedia/commons/6/6a/Applied_Materials_logo.svg",
  CMCSA: "https://upload.wikimedia.org/wikipedia/commons/9/9a/Comcast_logo.svg",
  TXN: "https://upload.wikimedia.org/wikipedia/commons/b/b3/Texas_Instruments_logo.svg",
  QCOM: "https://upload.wikimedia.org/wikipedia/commons/5/5b/Qualcomm-Logo.svg",
  PLTR: "https://upload.wikimedia.org/wikipedia/commons/1/1e/Palantir_Technologies_logo.svg",
  MU: "https://upload.wikimedia.org/wikipedia/commons/0/0c/Micron_Technology_logo.svg",
  GE: "https://upload.wikimedia.org/wikipedia/commons/f/ff/General_Electric_logo.svg",
  CAT: "https://upload.wikimedia.org/wikipedia/commons/9/9d/Caterpillar_logo.svg",
  IBM: "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg",
  UBER: "https://upload.wikimedia.org/wikipedia/commons/c/cc/Uber_logo_2018.svg",
  BA: "https://upload.wikimedia.org/wikipedia/commons/4/4f/Boeing_full_logo.svg",
  INTC: "https://upload.wikimedia.org/wikipedia/commons/c/c9/Intel-logo.svg",
  GS: "https://upload.wikimedia.org/wikipedia/commons/6/61/Goldman_Sachs.svg",
  MS: "https://upload.wikimedia.org/wikipedia/commons/1/1a/Morgan_Stanley_Logo.svg",
  SBUX: "https://upload.wikimedia.org/wikipedia/commons/d/d3/Starbucks_Corporation_Logo_2011.svg",

  "BTC-USD": "https://assets.coingecko.com/coins/images/1/large/bitcoin.png",
  "ETH-USD": "https://assets.coingecko.com/coins/images/279/large/ethereum.png",
  "SOL-USD": "https://assets.coingecko.com/coins/images/4128/large/solana.png",
  "BNB-USD": "https://assets.coingecko.com/coins/images/825/large/bnb-icon2_2x.png",
  "XRP-USD": "https://assets.coingecko.com/coins/images/44/large/xrp-symbol-white-128.png",
  "DOGE-USD": "https://assets.coingecko.com/coins/images/5/large/dogecoin.png",
  "ADA-USD": "https://assets.coingecko.com/coins/images/975/large/cardano.png",
  "THETA-USD": "https://assets.coingecko.com/coins/images/2538/large/theta-token-logo.png",
  "AVAX-USD": "https://assets.coingecko.com/coins/images/12559/large/Avalanche_Circle_RedWhite_Trans.png",
  "DOT-USD": "https://assets.coingecko.com/coins/images/12171/large/polkadot.png",
  "LINK-USD": "https://assets.coingecko.com/coins/images/877/large/chainlink-new-logo.png",
  "SHIB-USD": "https://assets.coingecko.com/coins/images/11939/large/shiba.png",
  "BCH-USD": "https://assets.coingecko.com/coins/images/780/large/bitcoin-cash-circle.png",
  "LTC-USD": "https://assets.coingecko.com/coins/images/2/large/litecoin.png",
  "NEAR-USD": "https://assets.coingecko.com/coins/images/10365/large/near.png",
  "UNI-USD": "https://assets.coingecko.com/coins/images/12504/large/uniswap-uni.png",
  "MATIC-USD": "https://assets.coingecko.com/coins/images/4713/large/polygon.png",
  "ICP-USD": "https://assets.coingecko.com/coins/images/14495/large/Internet_Computer_logo.png",
  "ETC-USD": "https://assets.coingecko.com/coins/images/453/large/ethereum-classic-logo.png",
  "FIL-USD": "https://assets.coingecko.com/coins/images/12817/large/filecoin.png",
  "XLM-USD": "https://assets.coingecko.com/coins/images/100/large/Stellar_symbol_black_RGB.png",
  "XMR-USD": "https://assets.coingecko.com/coins/images/69/large/monero_logo.png",
  "ATOM-USD": "https://assets.coingecko.com/coins/images/1481/large/cosmos_hub.png",
  "APT-USD": "https://assets.coingecko.com/coins/images/26455/large/aptos_round.png",
  "HBAR-USD": "https://assets.coingecko.com/coins/images/3688/large/hbar.png",
  "VET-USD": "https://assets.coingecko.com/coins/images/1167/large/VeChain-Logo-2018.png",
  "OP-USD": "https://assets.coingecko.com/coins/images/25244/large/Optimism.png",
  "ARB-USD": "https://assets.coingecko.com/coins/images/16547/large/arbitrum.png",
  "RNDR-USD": "https://assets.coingecko.com/coins/images/11636/large/rndr.png",
  "INJ-USD": "https://assets.coingecko.com/coins/images/12882/large/Injective_Logo.png",
  "STX-USD": "https://assets.coingecko.com/coins/images/2069/large/Stacks_logo_full.png",
  "KAS-USD": "https://assets.coingecko.com/coins/images/25751/large/kaspa.png",
  "FTM-USD": "https://assets.coingecko.com/coins/images/4001/large/Fantom.png",
  "AAVE-USD": "https://assets.coingecko.com/coins/images/12645/large/AAVE.png",
  "TIA-USD": "https://assets.coingecko.com/coins/images/31967/large/tia.jpg",
  "EGLD-USD": "https://assets.coingecko.com/coins/images/12335/large/egld-token-logo.png",
  "SAND-USD": "https://assets.coingecko.com/coins/images/12129/large/sandbox_logo.jpg",
  "MANA-USD": "https://assets.coingecko.com/coins/images/878/large/decentraland-mana.png",
  "EOS-USD": "https://assets.coingecko.com/coins/images/738/large/eos-eos-logo.png",
  "FLOW-USD": "https://assets.coingecko.com/coins/images/13446/large/flow_logo.png",
  "QNT-USD": "https://assets.coingecko.com/coins/images/3370/large/quant.png",
  "AXS-USD": "https://assets.coingecko.com/coins/images/13029/large/axie_infinity_logo.png",
  "MKR-USD": "https://assets.coingecko.com/coins/images/1364/large/Mark_Maker.png",
  "GRT-USD": "https://assets.coingecko.com/coins/images/13397/large/Graph_Token.png",
  "SNX-USD": "https://assets.coingecko.com/coins/images/3406/large/SNX.png",
  "GALA-USD": "https://assets.coingecko.com/coins/images/12493/large/GALA-COIN.png",
  "ALGO-USD": "https://assets.coingecko.com/coins/images/4380/large/download.png",
  "LDO-USD": "https://assets.coingecko.com/coins/images/13573/large/Lido_DAO.png",
  "KAVA-USD": "https://assets.coingecko.com/coins/images/9761/large/kava.png",
  "TRX-USD": "https://assets.coingecko.com/coins/images/1094/large/tron-logo.png",

  "^BVSP": "https://upload.wikimedia.org/wikipedia/commons/9/9e/B3_logo.svg",
  "^GSPC": "https://upload.wikimedia.org/wikipedia/commons/5/5d/SP_500_logo.svg",
  "^DJI": "https://upload.wikimedia.org/wikipedia/commons/2/2a/Dow_Jones_Industrial_Average_logo.svg",
  "^IXIC": "https://upload.wikimedia.org/wikipedia/commons/8/87/Nasdaq_Logo.svg",
  "^NDX": "https://upload.wikimedia.org/wikipedia/commons/8/87/Nasdaq_Logo.svg",
  "^FTSE": "https://upload.wikimedia.org/wikipedia/commons/4/44/FTSE_Russell_logo.svg",
  "^GDAXI": "https://upload.wikimedia.org/wikipedia/commons/1/1c/Deutsche_B%C3%B6rse_Logo.svg",
  "^FCHI": "https://upload.wikimedia.org/wikipedia/commons/3/36/Euronext_logo.svg",
  "^N225": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Nikkei_225_logo.svg",
  "^HSI": "https://upload.wikimedia.org/wikipedia/commons/1/15/Hang_Seng_Index_logo.svg",
  "^AXJO": "https://upload.wikimedia.org/wikipedia/commons/7/7c/ASX_logo.svg",
  "^NSEI": "https://upload.wikimedia.org/wikipedia/commons/5/59/National_Stock_Exchange_of_India_Logo.svg",
  "^GSPTSE": "https://upload.wikimedia.org/wikipedia/commons/2/2f/TMX_Group_logo.svg",
  "^STOXX50E": "https://upload.wikimedia.org/wikipedia/commons/7/77/STOXX_Logo.svg",
  "000001.SS": "https://upload.wikimedia.org/wikipedia/commons/0/0c/SSE_logo.svg",
  "399001.SZ": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Shenzhen_Stock_Exchange_logo.svg",
  "^SSMI": "https://upload.wikimedia.org/wikipedia/commons/3/3a/SIX_Group_logo.svg",
  "^KS11": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Korea_Exchange_logo.svg",
  "^STI": "https://upload.wikimedia.org/wikipedia/commons/6/6e/SGX_logo.svg",
  "^TWII": "https://upload.wikimedia.org/wikipedia/commons/5/55/Taiwan_Stock_Exchange_logo.svg",
};

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
    
    // 1. Check if we have a direct mapping for this ticker
    if (ASSET_LOGOS[ticker]) {
        logoImg.src = ASSET_LOGOS[ticker];
    } 
    // 2. Fallback to B3 repository if it's a Brazilian stock
    else {
        logoImg.src = `https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/${cleanTicker}.png`;
    }

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
    } else if (type === "days") {
      displayVal = parseFloat(value).toFixed(1) + " dias";
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
        ${createCard("Tempo Médio", t.avg_duration, "ri-timer-flash-line", "days")}
    `;
}

function renderTradeHistory(trades) {
  const tbody = document.getElementById("trade_history_body");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!trades || trades.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-secondary p-4">Nenhum trade realizado neste período.</td></tr>`;
    return;
  }

  // Reverse order (newest first)
  const sortedTrades = [...trades].sort((a, b) => new Date(b.entry_date) - new Date(a.entry_date));

  sortedTrades.forEach(trade => {
    const tr = document.createElement("tr");

    // Format dates
    const entryDate = new Date(trade.entry_date).toLocaleDateString("pt-BR");
    const exitDate = new Date(trade.exit_date).toLocaleDateString("pt-BR");
    
    // Values
    const retPct = (trade.return * 100).toFixed(2) + "%";
    const duration = trade.duration + " dias";

    // Styling based on result
    const isWin = trade.return > 0;
    const valClass = isWin ? "val-pos" : "val-neg";
    const statusBadge = isWin 
        ? `<span class="badge bg-green-lt">GAIN</span>` 
        : `<span class="badge bg-red-lt">LOSS</span>`;

    tr.innerHTML = `
        <td class="text-secondary">${entryDate}</td>
        <td>${parseFloat(trade.entry_price).toFixed(2)}</td>
        <td class="text-secondary">${exitDate}</td>
        <td>${parseFloat(trade.exit_price).toFixed(2)}</td>
        <td class="text-secondary">${duration}</td>
        <td class="text-end fw-bold ${valClass}">${retPct}</td>
        <td class="text-end">${statusBadge}</td>
    `;
    tbody.appendChild(tr);
  });
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
    renderTradeHistory(data.trade_stats.trades_list);

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

    for (const [key, categoryData] of Object.entries(allAssets)) {
      const opt = document.createElement("option");
      opt.value = key;
      opt.innerText = categoryData.label;
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
      
      if (data.error) {
        alert("Erro no Servidor: " + data.error);
        loading.style.display = "none";
        btn.disabled = false;
        return;
      }

      tableBody.innerHTML = "";
      data.forEach((item, index) => {
        const tr = document.createElement("tr");
        const isPositive = item.total_return > 0;

        tr.innerHTML = `
                    <td><span class="badge ${index < 3 ? "bg-yellow text-dark" : "bg-dark text-secondary"}">#${index + 1}</span></td>
                    <td class="fw-bold">${item.ticker}</td>
                    <td class="text-secondary small">${item.name}</td>
                    <td class="text-end fw-bold ${isPositive ? "val-profit" : "val-loss"}">${(item.total_return * 100).toFixed(2)}%</td>
                    <td class="text-end fw-bold">${item.sharpe.toFixed(2)}</td>
                    <td class="text-end val-loss">${(item.max_drawdown * 100).toFixed(2)}%</td>
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
  const modalEl = document.getElementById("modal_batch");
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();

  // 1. Atualizar Ticker Selecionado (Trigger + Hidden Input)
  document.getElementById("selected_ticker").value = ticker;
  document.getElementById("trigger_label").innerText = name;

  // 2. Disparar lógica de Seleção (Atualiza Logo e Badges do Topo)
  selectAsset(ticker, name);

  // 3. Executar o Backtest automaticamente
  runBacktest();

  // 4. Garantir que a área de resultados esteja visível
  document.getElementById("results_area").style.display = "flex";
};
