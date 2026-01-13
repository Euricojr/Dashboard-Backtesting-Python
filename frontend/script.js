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
    
    if (!chartElement) { console.error("Chart element not found"); return; }
    
    // Ensure container has dimensions
    if (chartElement.clientWidth === 0) {
        chartElement.style.width = '100%';
        chartElement.style.height = '500px';
    }

    // Configuração Premium do Gráfico
    const commonOptions = {
        layout: { 
            background: { type: 'solid', color: '#161b22' }, 
            textColor: '#d1d4dc',
            fontSize: 12,
            fontFamily: 'Inter, sans-serif'
        },
        grid: { 
            vertLines: { color: 'rgba(42, 46, 57, 0.3)' }, 
            horzLines: { color: 'rgba(42, 46, 57, 0.3)' } 
        },
        rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.3)' },
        timeScale: { borderColor: 'rgba(197, 203, 206, 0.3)', timeVisible: true },
        crosshair: { mode: 1 } // Normal Mode
    };

    try {
        mainChart = LightweightCharts.createChart(chartElement, commonOptions);
    } catch (e) {
        console.error("Failed to create chart:", e);
        return;
    }

    candleSeries = mainChart.addCandlestickSeries({
        upColor: '#26a69a', 
        downColor: '#ef5350', 
        borderVisible: false, 
        wickUpColor: '#26a69a', 
        wickDownColor: '#ef5350',
    });
    
    // SMA Series Initialization
    window.smaShortSeries = mainChart.addLineSeries({ color: '#ff9800', lineWidth: 2, title: 'SMA Curta' });
    window.smaLongSeries = mainChart.addLineSeries({ color: '#9c27b0', lineWidth: 2, title: 'SMA Longa' });
    
    // Split Line Series (Custom Scale to avoid messing with Price or RSI)
    window.vLineSeries = mainChart.addHistogramSeries({ 
        color: '#FFD700', 
        lastValueVisible: false, 
        priceScaleId: 'split_scale' 
    });
    // Configure hidden split scale
    mainChart.priceScale('split_scale').applyOptions({ visible: false, autoScale: true });
    
    // RSI default hidden
    mainChart.priceScale('left').applyOptions({ visible: false });

    // Performance Chart
    perfChart = LightweightCharts.createChart(perfElement, commonOptions);
    strategySeries = perfChart.addLineSeries({ color: '#00d4ff', lineWidth: 3, title: 'Estratégia' });
    assetSeries = perfChart.addLineSeries({ color: '#8b949e', lineWidth: 2, lineStyle: 2, title: 'Buy & Hold' });
    
    // RSI Integration (Same Chart)
    window.rsiSeries = mainChart.addLineSeries({ 
        color: '#7E57C2', 
        lineWidth: 2, 
        priceScaleId: 'left',
        title: 'RSI (14)'
    });
    // Levels will be added via createPriceLine dynamically


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
    const strategy = document.getElementById('strategy_select').value;
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
            body: JSON.stringify({ ticker, start, end, strategy, sma_short: smaShort, sma_long: smaLong })
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

        // RSI Data Handler (Panel Merge)
        if (data.rsi_data && data.rsi_data.length > 0) {
            // Mode: RSI Active (Two Panels on One Chart)
            
            // 1. Squish Candles Up to make room
            mainChart.priceScale('right').applyOptions({
                scaleMargins: { top: 0.1, bottom: 0.30 }
            });
            
            // 2. Enable RSI Scale at Bottom (Left Axis)
            mainChart.priceScale('left').applyOptions({
                visible: true,
                scaleMargins: { top: 0.75, bottom: 0 }
            });
            
            // 3. Set Data
            window.rsiSeries.setData(data.rsi_data);
            
            // 4. Add Levels
            // Removing previous lines if tracked would be ideal, but for now we re-create.
            window.rsiSeries.createPriceLine({ price: 70, color: '#ef5350', lineWidth: 1, lineStyle: 2, axisLabelVisible: false });
            window.rsiSeries.createPriceLine({ price: 35, color: '#26a69a', lineWidth: 1, lineStyle: 2, axisLabelVisible: false });

        } else {
            // Mode: SMA / No RSI (Full Chart)
            
            // 1. Reset Candles to Full Height
            mainChart.priceScale('right').applyOptions({
                scaleMargins: { top: 0.1, bottom: 0.1 }
            });
            
            // 2. Hide RSI Scale
            mainChart.priceScale('left').applyOptions({
                visible: false
            });
            
            // 3. Clear RSI Data
            window.rsiSeries.setData([]);
        }

        if (data.equity_data) {
            strategySeries.setData(data.equity_data.map(d => ({ time: d.time, value: d.strategy })));
            assetSeries.setData(data.equity_data.map(d => ({ time: d.time, value: d.asset })));
            perfChart.timeScale().fitContent();
        }

        const mIn = data.metrics_in;
        const mOut = data.metrics_out;
        
        // Update Table Cells
        // In-Sample
        document.getElementById('td_total_in').innerText = mIn.total_return;
        document.getElementById('td_cagr_in').innerText = mIn.cagr;
        document.getElementById('td_sharpe_in').innerText = mIn.sharpe_ratio;
        document.getElementById('td_vol_in').innerText = mIn.volatilidade_anual;
        document.getElementById('td_dd_in').innerText = mIn.max_drawdown;

        // Out-of-Sample
        document.getElementById('td_total_out').innerText = mOut.total_return;
        document.getElementById('td_cagr_out').innerText = mOut.cagr;
        document.getElementById('td_sharpe_out').innerText = mOut.sharpe_ratio;
        document.getElementById('td_vol_out').innerText = mOut.volatilidade_anual;
        document.getElementById('td_dd_out').innerText = mOut.max_drawdown;
        
        const aiBox = document.getElementById('ai_analysis');
        if (aiBox) {
            aiBox.innerHTML = data.ai_analysis;
            aiBox.className = "p-3 " + (data.is_warning ? "bg-warning-lt" : "bg-success-lt");
        }

        document.getElementById('results_area').style.display = 'block';

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
    
    // Strategy Logic
    const strategySelect = document.getElementById('strategy_select');
    const smaSettings = document.getElementById('sma_settings');
    
    strategySelect.addEventListener('change', () => {
        if (strategySelect.value === 'SMA') {
            smaSettings.style.display = 'block';
        } else {
            smaSettings.style.display = 'none';
        }
    });
});
