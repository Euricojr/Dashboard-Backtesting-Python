document.addEventListener('DOMContentLoaded', async () => {
    // 1. Identificar Ticker da URL (Sem default forçado para permitir escolha inicial)
    const urlParams = new URLSearchParams(window.location.search);
    let ticker = urlParams.get('ticker'); // Null se não tiver parametro
    
    // Setup inicial
    const searchInput = document.getElementById('ticker-search');
    const searchBtn = document.getElementById('search-btn');
    
    // Se tiver ticker na URL, preenche input e carrega
    if (ticker) {
        if (searchInput) searchInput.value = ticker;
        await loadFundamentals(ticker);
    } else {
        // Estado Inicial: Foco na busca para o usuário digitar
        if (searchInput) searchInput.focus();
        document.querySelector('.asset-ticker').innerText = "";
    }
    
    // --- Eventos de Busca ---
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            handleSearch(searchInput.value);
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSearch(searchInput.value);
        });
    }
});

function handleSearch(query) {
    const newTicker = query.trim().toUpperCase();
    if (newTicker) {
        // Atualiza URL sem recarregar
        const newUrl = `${window.location.pathname}?ticker=${newTicker}`;
        window.history.pushState({path: newUrl}, '', newUrl);
        // Busca novos dados
        loadFundamentals(newTicker);
    }
}

async function loadFundamentals(ticker) {
    // UI Loading
    document.querySelector('.asset-ticker').innerText = ticker;
    // Opcional: Spinner ou Opacidade
    document.body.style.cursor = 'wait';
    document.querySelectorAll('.metric-value').forEach(el => el.innerText = '...');
    
    try {
        const response = await fetch(`/api/fundamentos?ticker=${ticker}`);
        
        if (!response.ok) {
            throw new Error(`Erro API: ${response.status}`);
        }
        
        const data = await response.json();
        renderDashboard(data, ticker);

    } catch (error) {
        console.error("Erro Fatal:", error);
        alert(`Falha ao carregar dados para ${ticker}. Verifique se o ativo existe na CVM.`);
        document.querySelectorAll('.metric-value').forEach(el => el.innerText = '-');
    } finally {
        document.body.style.cursor = 'default';
    }
}

function renderDashboard(data, requestedTicker = null) {
    console.log("Dados Recebidos:", data);

    // --- Header Update (Hero Section) ---
    // Atualiza Nome da Empresa e Preço se disponíveis
    if (data.meta && data.meta.empresa_cvm) {
        const h1 = document.getElementById('asset-header');
        if (h1) {
            const tickerText = requestedTicker ? requestedTicker : "---";
            h1.innerHTML = `${toTitleCase(data.meta.empresa_cvm)} <span class="asset-ticker">${tickerText}</span>`;
        }
    }
    
    // Mostra o bloco de preço (estava oculto)
    const priceBlock = document.getElementById('price-header');
    if (priceBlock) priceBlock.style.visibility = 'visible';
    

    
    // Atualiza Preço na Hero Section
    // Agora o backend retorna 'price' explicitamente.
    let currentPrice = data.price;
    
    // Fallback apenas se não vier do backend (ex: cache antigo)
    if (!currentPrice && data.valuation && data.valuation['LPA'] && data.valuation['P/L']) {
        currentPrice = data.valuation['LPA'] * data.valuation['P/L'];
    }
    
    if (currentPrice !== undefined && currentPrice !== null) {
        const priceEl = document.querySelector('.current-price');
        // Formatar BRL corretamente
        if (priceEl) priceEl.innerText = currentPrice.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }
    
    // --- Preencher Cards ---
    updateCard('P/L', data.valuation['P/L'], false);
    updateCard('P/VP', data.valuation['P/VP'], false);
    updateCard('EV/EBITDA', data.valuation['EV_Ebitda'], false);
    updateCard('LPA', data.valuation['LPA'], false);
    updateCard('VPA', data.valuation['VPA'], false);
    
    // Div Yield não vem no JSON atual do backend (precisaria de dividendos). 
    // Vamos deixar placeholder ou calcular se tiver dados. Backend não mandou. Deixar '-'
    updateCard('Div. Yield', '-', true); 

    updateCard('Dív. Liq / EBITDA', data.endividamento['DivLiq_Ebitda'], false);
    updateCard('Liquidez Corr.', data.endividamento['Liq_Corrente'], false);
    
    updateCard('Dívida Bruta', formatCurrency(data.endividamento['Div_Bruta']), false, true);
    // Disponibilidades = Caixa
    // Div Liquida = Div Bruta - Caixa -> Caixa = Div Bruta - Div Liquida
    // Mas no raw tem 'divida_bruta' e calculamos 'divida_liquida' no backend.
    // Backend não retornou 'caixa_equivalentes' direto no raw, mas tem no 'ativo_total'
    // Vamos procurar se podemos deduzir. DivLiq = DivBruta - Caixa.
    // No backend: divida_liquida = divida_bruta - caixa_equivalentes.
    // Logo, temos que pedir pro backend mandar o caixa ou a gente infere.
    // O backend retorna 'raw' com alguns dados. Vamos usar o que tem.
    
    updateCard('Margem Bruta', data.eficiencia['Margem_Bruta'], true);
    updateCard('Margem Líquida', data.eficiencia['Margem_Liquida'], true);
    updateCard('ROE', data.eficiencia['ROE'], true);
    
    // ROIC não veio.
    updateCard('ROIC', '-', true);

    // --- Heatmap (Bordas Coloridas) ---
    applyHeatmapRules(data);

    // --- Gráficos ---
    renderCharts(data);
}

function updateCard(label, value, isPercent, isCurrency = false) {
    // Acha o card pelo label (meio frágil, melhor seria IDs, mas o HTML não tem IDs nos cards)
    // Vamos iterar
    const cards = Array.from(document.querySelectorAll('.metric-card'));
    const target = cards.find(c => c.querySelector('.metric-label').innerText.includes(label.toUpperCase()) || c.querySelector('.metric-label').innerText === label);
    
    if (target) {
        const valEl = target.querySelector('.metric-value');
        if (value === '-' || value === undefined) {
            valEl.innerText = '-';
            return;
        }
        
        if (isCurrency && typeof value === 'number') {
            valEl.innerText = formatCurrency(value); // R$ Bilhões
        } else if (isPercent) {
            valEl.innerHTML = `${value}<span class="metric-unit">%</span>`;
        } else {
            valEl.innerText = value;
        }
    }
}

function formatCurrency(val) {
    if (val > 1000000000) return `R$ ${(val/1000000000).toFixed(1)}B`;
    if (val > 1000000) return `R$ ${(val/1000000).toFixed(1)}M`;
    return `R$ ${val}`;
}

function applyHeatmapRules(data) {
    // Define helper para colorir
    const colorize = (label, conditionGood, conditionBad) => {
        const cards = Array.from(document.querySelectorAll('.metric-card'));
        const target = cards.find(c => c.querySelector('.metric-label').innerText.includes(label.toUpperCase()));
        if (!target) return;
        
        const bar = target.querySelector('.quality-bar');
        bar.className = 'quality-bar'; // reset
        
        // Pega valor numérico do DOM se possível ou do data source
        // Vamos usar o data source mapping manual
        let val = null;
        
        if (label === 'P/L') val = data.valuation['P/L'];
        if (label === 'ROE') val = data.eficiencia['ROE'];
        if (label === 'Margem Líquida') val = data.eficiencia['Margem_Liquida'];
        if (label === 'Dív. Liq / EBITDA') val = data.endividamento['DivLiq_Ebitda'];

        if (val !== null) {
             if (conditionGood(val)) bar.classList.add('qb-good');
             else if (conditionBad(val)) bar.classList.add('qb-bad');
             else bar.classList.add('qb-neutral');
        }
    };

    colorize('P/L', v => v > 0 && v < 15, v => v < 0 || v > 30);
    colorize('ROE', v => v > 15, v => v < 5);
    colorize('Margem Líquida', v => v > 10, v => v < 2);
    colorize('Dív. Liq / EBITDA', v => v < 2.5, v => v > 3.5);
}

function renderCharts(data) {
    // Gráfico 1: Receita vs Lucro vs EBITDA
    const options1 = {
        series: [{
            name: 'Receita Líquida',
            data: [data.raw.receita_liquida]
        }, {
            name: 'EBITDA',
            data: [data.raw.ebitda]
        }, {
            name: 'Lucro Líquido',
            data: [data.raw.lucro_liquido]
        }],
        chart: {
            type: 'bar',
            height: 350,
            toolbar: { show: false },
            background: 'transparent'
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '55%',
                endingShape: 'rounded'
            },
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            show: true,
            width: 2,
            colors: ['transparent']
        },
        xaxis: {
            categories: ['Último Ano'],
            labels: { style: { colors: '#a1a1aa' } }
        },
        yaxis: {
            labels: { 
                style: { colors: '#a1a1aa' },
                formatter: (val) => { return (val / 1000000000).toFixed(0) + "B" }
            }
        },
        fill: {
            opacity: 1
        },
        colors: ['#00E396', '#775DD0', '#FEB019'],
        theme: { mode: 'dark' },
        title: {
            text: 'Resultados (R$)',
            align: 'left',
            style: { color: '#a1a1aa' }
        }
    };

    const chart1 = new ApexCharts(document.querySelector("#chart-results"), options1);
    chart1.render();

    // Gráfico 2: Estrutura de Capital (Donut)
    // Dívida vs Patrimônio
    const options2 = {
        series: [data.raw.patrimonio_liquido, data.raw.divida_bruta],
        chart: {
            type: 'donut',
            height: 350,
            background: 'transparent'
        },
        labels: ['Patrimônio Líquido', 'Dívida Bruta'],
        colors: ['#008FFB', '#FF4560'],
        stroke: { show: false },
        dataLabels: { enabled: false },
        legend: {
            position: 'bottom',
            labels: { colors: '#a1a1aa' }
        },
        title: {
            text: 'Estrutura de Capital',
            align: 'left',
            style: { color: '#a1a1aa' }
        },
        tooltip: {
            y: {
                formatter: function (val) {
                    return "R$ " + (val / 1000000000).toFixed(1) + " B"
                }
            }
        }
    };

    const chart2 = new ApexCharts(document.querySelector("#chart-debt"), options2);
    chart2.render();
}

function toTitleCase(str) {
    return str.replace(
        /\w\S*/g,
        function(txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}
