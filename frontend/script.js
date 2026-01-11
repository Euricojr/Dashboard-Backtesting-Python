// Dashboard Quantitative Script
// Optimized with Command Palette (Modal Search)

let mainChart;
let candleSeries;
let perfChart;
let strategySeries;
let assetSeries;
let allAssets = {};

// --- INICIALIZAÇÃO ---

async function loadAssets() {
    try {
        const res = await fetch('http://localhost:5000/assets');
        allAssets = await res.json();
        
        const trigger = document.getElementById('sidebar_trigger');
        const modal = document.getElementById('search_modal');
        const searchInput = document.getElementById('modal_search_input');

        // Abre o Modal
        const openModal = () => {
            modal.style.display = 'flex';
            searchInput.value = '';
            renderModalResults("");
            // Pequeno delay para o focus funcionar bem no modal
            setTimeout(() => searchInput.focus(), 100);
        };

        const closeModal = () => {
            modal.style.display = 'none';
        };

        trigger.addEventListener('click', openModal);

        // Atalhos de teclado
        document.addEventListener('keydown', (e) => {
            // Cmd/Ctrl + K para abrir
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                openModal();
            }
            // ESC para fechar
            if (e.key === 'Escape') closeModal();
        });

        // Fechar ao clicar fora do conteúdo
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal();
        });

        searchInput.addEventListener('input', (e) => renderModalResults(e.target.value));

    } catch (err) {
        console.error("Erro ao carregar ativos:", err);
    }
}

function renderModalResults(query) {
    const resultsDiv = document.getElementById('modal_results');
    const q = query.toLowerCase();
    resultsDiv.innerHTML = '';
    
    let hasResults = false;

    for (const [category, stocks] of Object.entries(allAssets)) {
        const filtered = Object.entries(stocks).filter(([ticker, name]) => 
            ticker.toLowerCase().includes(q) || name.toLowerCase().includes(q)
        );

        if (filtered.length > 0) {
            hasResults = true;
            const group = document.createElement('div');
            group.className = 'search-modal-group';
            group.innerText = category;
            resultsDiv.appendChild(group);

            filtered.forEach(([ticker, name]) => {
                const item = document.createElement('div');
                item.className = 'search-modal-item';
                item.innerHTML = `<span>${name}</span> <span class="ticker text-info">${ticker}</span>`;
                item.onclick = () => selectAsset(ticker, name);
                resultsDiv.appendChild(item);
            });
        }
    }

    // Modal Option for Custom Search
    const otherItem = document.createElement('div');
    otherItem.className = 'search-modal-item fw-bold text-accent';
    otherItem.style.color = 'var(--accent)';
    otherItem.innerHTML = '<span>🔍 PESQUISAR OUTRO TICKER...</span> <span class="ticker">ANY</span>';
    otherItem.onclick = () => selectAsset("SEARCH_OTHER", "Pesquisar Outro...");
    resultsDiv.appendChild(otherItem);
}

function selectAsset(ticker, name) {
    const label = document.getElementById('trigger_label');
    const hidden = document.getElementById('selected_ticker');
    const customDiv = document.getElementById('custom_ticker_div');
    const modal = document.getElementById('search_modal');

    label.innerText = name;
    hidden.value = ticker;
    modal.style.display = 'none';

    customDiv.style.display = (ticker === "SEARCH_OTHER") ? "block" : "none";
}

function initChart() {
    const chartElement = document.getElementById('chart');
    const perfElement = document.getElementById('perf_chart');
    
    // Configuração Premium do Gráfico
    const commonOptions = {
        layout: { 
            background: { type: 'solid', color: '#161b22' }, 
            textColor: '#d1d4dc',
            fontSize: 12,
            fontFamily: 'Outfit, sans-serif'
        },
        grid: { 
            vertLines: { color: 'rgba(42, 46, 57, 0.3)' }, 
            horzLines: { color: 'rgba(42, 46, 57, 0.3)' } 
        },
        rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.3)' },
        timeScale: { borderColor: 'rgba(197, 203, 206, 0.3)' },
    };

    mainChart = LightweightCharts.createChart(chartElement, commonOptions);

    candleSeries = mainChart.addCandlestickSeries({
        upColor: '#26a69a', 
        downColor: '#ef5350', 
        borderVisible: false, 
        wickUpColor: '#26a69a', 
        wickDownColor: '#ef5350',
    });
    
    // SMA Series Initialization
    window.smaShortSeries = mainChart.addLineSeries({
        color: '#ff9800', // Laranja
        lineWidth: 2,
        title: 'SMA Curta'
    });

    window.smaLongSeries = mainChart.addLineSeries({
        color: '#9c27b0', // Roxo
        lineWidth: 2,
        title: 'SMA Longa'
    });
    
    window.vLineSeries = mainChart.addHistogramSeries({ 
        color: '#FFD700', 
        lastValueVisible: false, 
        priceScaleId: 'left' 
    });
    mainChart.priceScale('left').applyOptions({ visible: false });

    perfChart = LightweightCharts.createChart(perfElement, commonOptions);

    strategySeries = perfChart.addLineSeries({ 
        color: '#00d4ff', 
        lineWidth: 3, 
        title: 'Estratégia' 
    });
    assetSeries = perfChart.addLineSeries({ 
        color: '#8b949e', 
        lineWidth: 2, 
        lineStyle: 2, 
        title: 'Buy & Hold' 
    });

    const handleResize = () => {
        mainChart.resize(chartElement.clientWidth, chartElement.clientHeight);
        perfChart.resize(perfElement.clientWidth, perfElement.clientHeight);
    };
    window.addEventListener('resize', handleResize);
    // Garantir resize inicial após carregamento
    setTimeout(handleResize, 500);
}

function formatPct(val) {
    if (!val && val !== 0) return '0.00%';
    return (val * 100).toFixed(2) + '%';
}

async function runBacktest() {
    let ticker = document.getElementById('selected_ticker').value;
    
    if (ticker === "SEARCH_OTHER") {
        ticker = document.getElementById('custom_ticker').value.toUpperCase();
        if (!ticker) { alert("Digite um ticker!"); return; }
    }

    const start = document.getElementById('start_date').value;
    const end = document.getElementById('end_date').value;
    const smaShort = document.getElementById('sma_short').value;
    const smaLong = document.getElementById('sma_long').value;
    const btn = document.getElementById('run_btn');

    btn.disabled = true;
    btn.classList.add('opacity-50');
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> PROCESSANDO...';

    try {
        const response = await fetch('http://localhost:5000/run_backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, start, end, sma_short: smaShort, sma_long: smaLong })
        });

        const data = await response.json();
        if (data.error) { 
            alert("Erro: " + data.error); 
            btn.disabled = false; 
            btn.classList.remove('opacity-50');
            btn.innerText = "EXECUTAR BACKTEST"; 
            return; 
        }

        document.getElementById('chart_placeholder').style.display = 'none';

        candleSeries.setData(data.candle_data);
        
        // Plot SMAs
        if (data.sma_short_data) window.smaShortSeries.setData(data.sma_short_data);
        if (data.sma_long_data) window.smaLongSeries.setData(data.sma_long_data);

        let finalMarkers = [...data.markers];
        if (data.split_date) {
            window.vLineSeries.setData([{ time: data.split_date, value: 1000000000 }]);
            finalMarkers.push({ 
                time: data.split_date, 
                position: 'aboveBar', 
                color: '#FFD700', 
                shape: 'arrowDown', 
                text: 'Fim In-Sample', 
                size: 2 
            });
        }
        candleSeries.setMarkers(finalMarkers);
        mainChart.timeScale().fitContent();

        if (data.perf_data) {
            strategySeries.setData(data.perf_data.map(d => ({ time: d.time, value: d.strategy })));
            assetSeries.setData(data.perf_data.map(d => ({ time: d.time, value: d.asset })));
            perfChart.timeScale().fitContent();
        }

        const mIS = data.metrics_is;
        const mOOS = data.metrics_oos;
        const tableBody = document.getElementById('metrics_table_body');
        
        const metricsList = [
            { label: "Retorno Total", key: "Total Return", isPct: true },
            { label: "CAGR", key: "CAGR", isPct: true },
            { label: "Volatilidade Anual", key: "Vol Anual", isPct: true },
            { label: "Sharpe Ratio", key: "Sharpe Ratio", isPct: false },
            { label: "Max Drawdown", key: "Max Drawdown", isPct: true }
        ];

        tableBody.innerHTML = '';
        metricsList.forEach(m => {
            const row = document.createElement('tr');
            const valIS = m.isPct ? formatPct(mIS[m.key]) : (mIS[m.key] || 0).toFixed(2);
            const valOOS = m.isPct ? formatPct(mOOS[m.key]) : (mOOS[m.key] || 0).toFixed(2);
            row.innerHTML = `<td>${m.label}</td><td class="fw-bold">${valIS}</td><td class="fw-bold text-info">${valOOS}</td>`;
            tableBody.appendChild(row);
        });

        document.getElementById('m_total').innerText = formatPct(mOOS['Total Return']);
        document.getElementById('m_sharpe').innerText = (mOOS['Sharpe Ratio'] || 0).toFixed(2);
        
        const aiBox = document.getElementById('ai_container');
        aiBox.innerHTML = data.ai_analysis;
        aiBox.className = "ai-box " + (data.is_warning ? "ai-warning" : "ai-info");

        document.getElementById('results_area').style.display = 'block';
        document.getElementById('quick_metrics').style.display = 'block';

    } catch (err) {
        console.error(err);
        alert("Falha de conexão com o servidor!");
    } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-50');
        btn.innerHTML = "EXECUTAR BACKTEST";
        // Forçar resize final para garantir layout perfeito
        setTimeout(() => {
            const chartDiv = document.getElementById('chart');
            const perfDiv = document.getElementById('perf_chart');
            
            if (chartDiv) mainChart.resize(chartDiv.clientWidth, 500);
            if (perfDiv && perfDiv.offsetParent !== null) {
                // Checa se está visível
                perfChart.resize(perfDiv.clientWidth, 350);
                perfChart.timeScale().fitContent();
            }
        }, 100);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadAssets();
    document.getElementById('run_btn').addEventListener('click', runBacktest);
});
