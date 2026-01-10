let chart;
let candlestickSeries;

// --- INICIALIZAÇÃO ---

async function loadAssets() {
    try {
        const res = await fetch('http://localhost:5000/assets');
        const categories = await res.json();
        const select = document.getElementById('asset_select');
        select.innerHTML = ''; // Limpa

        for (const [category, stocks] of Object.entries(categories)) {
            const group = document.createElement('optgroup');
            group.label = category;
            
            for (const [ticker, name] of Object.entries(stocks)) {
                const opt = document.createElement('option');
                opt.value = ticker;
                opt.innerText = name;
                group.appendChild(opt);
            }
            select.appendChild(group);
        }

        const searchOpt = document.createElement('option');
        searchOpt.value = "SEARCH_OTHER";
        searchOpt.innerText = "🔍 PESQUISAR OUTRO...";
        select.appendChild(searchOpt);

    } catch (err) {
        console.error("Erro ao carregar ativos:", err);
    }
}

function initChart() {
    const chartElement = document.getElementById('chart');
    chart = LightweightCharts.createChart(chartElement, {
        layout: {
            background: { type: 'solid', color: '#161b22' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
            horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.8)' },
        timeScale: { borderColor: 'rgba(197, 203, 206, 0.8)' },
    });

    try {
        // Método estável para a versão 3.8.0
        candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        // Séria oculta para a linha vertical (divisor IS/OOS)
        window.vLineSeries = chart.addHistogramSeries({
            color: '#FFD700',
            lastValueVisible: false,
            priceScaleId: 'left', // Usa a escala da esquerda para não conflitar
        });
        
        chart.priceScale('left').applyOptions({
            visible: false, // Esconde a escala
        });

        console.log("Série de Candlestick adicionada.");
    } catch (e) {
        // Handle error if series cannot be added
        console.error("Erro ao adicionar séries ao gráfico:", e);
    }

    window.addEventListener('resize', () => {
        chart.resize(chartElement.clientWidth, chartElement.clientHeight);
    });
}

// --- LÓGICA DO BACKTEST ---

function formatPct(val) {
    return (val * 100).toFixed(2) + '%';
}

async function runBacktest() {
    const select = document.getElementById('asset_select');
    let ticker = select.value;
    
    if (ticker === "SEARCH_OTHER") {
        ticker = document.getElementById('custom_ticker').value.toUpperCase();
        if (!ticker) { alert("Digite um ticker!"); return; }
    }

    const start = document.getElementById('start_date').value;
    const end = document.getElementById('end_date').value;
    const btn = document.getElementById('run_btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> PROCESSANDO...';

    try {
        const response = await fetch('http://localhost:5000/run_backtest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker, start, end })
        });

        const data = await response.json();
        if (data.error) { alert("Erro: " + data.error); btn.disabled = false; btn.innerText = "🚀 EXECUTAR BACKTEST"; return; }

        // 1. Atualiza Gráfico
        candlestickSeries.setData(data.candle_data);
        
        // Adiciona os Marcadores (Compra/Venda + Divisor)
        let finalMarkers = [...data.markers];
        if (data.split_date) {
            // Desenha a linha vertical usando o histograma gigante
            window.vLineSeries.setData([{ time: data.split_date, value: 1000000000 }]);
            
            // Adiciona um marcador de texto para a divisão
            finalMarkers.push({
                time: data.split_date,
                position: 'aboveBar',
                color: '#FFD700',
                shape: 'arrowDown',
                text: 'Fim In-Sample',
                size: 2
            });
        }
        
        candlestickSeries.setMarkers(finalMarkers);
        chart.timeScale().fitContent();

        // 2. Tabela de Métricas
        const mIS = data.metrics_is;
        const mOOS = data.metrics_oos;
        const tableBody = document.getElementById('metrics_table_body');
        
        const metrics = [
            { label: "Retorno Total", key: "Total Return", isPct: true },
            { label: "CAGR", key: "CAGR", isPct: true },
            { label: "Volatilidade", key: "Vol Anual", isPct: true },
            { label: "Sharpe Ratio", key: "Sharpe Ratio", isPct: false },
            { label: "Max Drawdown", key: "Max Drawdown", isPct: true }
        ];

        tableBody.innerHTML = '';
        metrics.forEach(m => {
            const row = document.createElement('tr');
            const valIS = m.isPct ? formatPct(mIS[m.key]) : mIS[m.key].toFixed(2);
            const valOOS = m.isPct ? formatPct(mOOS[m.key]) : mOOS[m.key].toFixed(2);
            
            row.innerHTML = `<td>${m.label}</td><td class="fw-bold">${valIS}</td><td class="fw-bold text-accent">${valOOS}</td>`;
            tableBody.appendChild(row);
        });

        // 3. UI Updates
        document.getElementById('m_total').innerText = formatPct(mOOS['Total Return']);
        document.getElementById('m_sharpe').innerText = mOOS['Sharpe Ratio'].toFixed(2);
        
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
        btn.innerHTML = "🚀 EXECUTAR BACKTEST";
    }
}

// --- EVENTOS ---

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadAssets();
    
    document.getElementById('run_btn').addEventListener('click', runBacktest);
    
    document.getElementById('asset_select').addEventListener('change', (e) => {
        const customDiv = document.getElementById('custom_ticker_div');
        customDiv.style.display = (e.target.value === "SEARCH_OTHER") ? "block" : "none";
    });
});
