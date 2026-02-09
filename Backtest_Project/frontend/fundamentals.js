let allAssets = {};
let dividendChart = null;

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

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Identificar Ticker da URL
    const urlParams = new URLSearchParams(window.location.search);
    let ticker = urlParams.get('ticker');
    
    // Setup inicial
    await loadAssets();
    
    const trigger = document.getElementById('search-trigger');
    const modal = document.getElementById('search_modal');
    const searchInput = document.getElementById('modal_search_input');
    
    if (trigger) {
        trigger.addEventListener('click', () => {
            modal.style.display = 'flex';
            searchInput.value = '';
            renderModalResults('');
            setTimeout(() => searchInput.focus(), 100);
        });
    }

    searchInput.addEventListener('input', (e) => renderModalResults(e.target.value));

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            trigger.click();
        }
        if (e.key === 'Escape') {
            modal.style.display = 'none';
        }
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    // Se tiver ticker na URL, carrega
    if (ticker) {
        document.getElementById('trigger-label').innerText = ticker.toUpperCase();
        await loadFundamentals(ticker);
    }
    
    // Help Icon Click Handler (Mobile/Desktop) -> Open Modal
    document.addEventListener('click', (e) => {
        const icon = e.target.closest('.help-icon');
        
        if (icon) {
            e.stopPropagation();
            e.preventDefault();
            
            // Get content
            const tooltipText = icon.getAttribute('data-tooltip');
            // Title is strictly the text inside the metric label span
            let titleText = 'Indicador';
            try {
                // The icon is inside .metric-label, which has a span with the text
                const labelSpan = icon.closest('.metric-label').querySelector('span');
                if (labelSpan) titleText = labelSpan.textContent.trim();
            } catch (err) {
                console.warn("Could not extract title", err);
            }

            openMetricModal(titleText, tooltipText);
        }
        
        // Close modal on outside click
        const modal = document.getElementById('metric-info-modal');
        if (modal && e.target === modal) {
            closeMetricModal();
        }
    });

});

function openMetricModal(title, description) {
    const modal = document.getElementById('metric-info-modal');
    const titleEl = document.getElementById('metric-modal-title');
    const descEl = document.getElementById('metric-modal-desc');
    
    if (modal && titleEl && descEl) {
        titleEl.innerText = title;
        descEl.innerText = description;
        modal.style.display = 'flex';
        // Add minimal animation class if desired
        setTimeout(() => modal.classList.add('show'), 10);
    }
}

function closeMetricModal() {
    const modal = document.getElementById('metric-info-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300); // Wait for transition
    }
}

async function loadAssets() {
    try {
        const res = await fetch("/assets");
        allAssets = await res.json();
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
            group.className = "search-modal-group";
            group.innerText = categoryData.label;
            resultsDiv.appendChild(group);

            filtered.forEach(([ticker, name]) => {
                const item = document.createElement("div");
                item.className = "list-group-item-dark";
                item.innerHTML = `
                    <div class="d-flex flex-column">
                        <span class="fw-bold text-white">${name}</span>
                        <span class="text-secondary small">${categoryData.label}</span>
                    </div>
                    <span class="badge bg-green-lt">${ticker}</span>
                `;
                item.onclick = () => {
                    document.getElementById('search_modal').style.display = 'none';
                    document.getElementById('trigger-label').innerText = ticker;
                    handleSearch(ticker);
                };
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

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function resetDashboard() {
    const tickerEl = document.getElementById('display_ticker');
    const nameEl = document.getElementById('display_name');
    const logoImg = document.getElementById('asset_logo');
    const logoPlaceholder = document.getElementById('asset_icon_placeholder');
    const badges = document.getElementById('asset_badges_container');
    const description = document.getElementById('display_description');
    const website = document.getElementById('display_website');

    if (tickerEl) tickerEl.innerText = "---";
    if (nameEl) nameEl.innerText = "Selecione um Ativo";
    if (badges) badges.style.display = 'none';
    if (description) description.innerText = "Selecione um ativo para ver o sumário do modelo de negócio.";
    if (website) website.style.display = 'none';
    
    if (logoImg) {
        logoImg.style.display = 'none';
        logoImg.src = '';
    }
    if (logoPlaceholder) logoPlaceholder.style.display = 'block';
    
    const priceBlock = document.getElementById('price-header');
    if (priceBlock) priceBlock.style.visibility = 'hidden';

    // Limpa todos os cards
    const metricValues = document.querySelectorAll('.metric-value');
    if (metricValues) metricValues.forEach(el => el.innerText = '-');

    const qualityBars = document.querySelectorAll('.quality-bar');
    if (qualityBars) qualityBars.forEach(el => el.className = 'quality-bar');

    if (dividendChart) {
      dividendChart.destroy();
      dividendChart = null;
    }

    const marketStrip = document.getElementById('market_strip');
    if (marketStrip) marketStrip.style.display = 'none';

    const newsContainer = document.getElementById('news-container');
    const newsTitle = document.getElementById('news-section-title');
    if (newsContainer) {
        newsContainer.innerHTML = '';
        newsContainer.style.display = 'none';
    }
    if (newsTitle) newsTitle.style.display = 'none';
}

async function loadFundamentals(ticker) {
    showLoading();
    const tickerDisplay = document.getElementById('display_ticker');
    if (tickerDisplay) tickerDisplay.innerText = ticker.toUpperCase();
    
    try {
        const response = await fetch(`/api/fundamentos?ticker=${ticker}`);
        if (!response.ok) throw new Error(`Erro API: ${response.status}`);
        const data = await response.json();
        renderDashboard(data, ticker);
    } catch (error) {
        console.error("Erro Fatal:", error);
        alert(`Falha ao carregar dados para ${ticker}. Verifique se o ativo existe.`);
        resetDashboard();
    } finally {
        setTimeout(() => hideLoading(), 300);
    }
}

function renderDashboard(data, requestedTicker = null) {
    console.log("Dados Recebidos:", data);

    // --- Market Strip ---
    const marketStrip = document.getElementById('market_strip');
    if (marketStrip && data.mercado) {
        marketStrip.style.display = 'flex';
        
        // Min/Máx
        document.getElementById('strip_min_52').innerText = (data.mercado.min_52sem || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        document.getElementById('strip_max_52').innerText = (data.mercado.max_52sem || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        
        document.getElementById('strip_min_mes').innerText = (data.mercado.min_mes || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        document.getElementById('strip_max_mes').innerText = (data.mercado.max_mes || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        // DY
        const dy = data.valuation['Div_Yield'] || 0;
        const dyEl = document.getElementById('strip_dy');
        dyEl.innerText = `${dy.toFixed(2)}%`;
        dyEl.className = `market-strip-value ${dy > 0 ? 'text-green' : ''}`;

        // Valorização 12M e Mês
        const val12m = data.mercado.valorizacao_12m || 0;
        const val12mEl = document.getElementById('strip_val_12m');
        val12mEl.innerHTML = `${val12m > 0 ? '<i class="ri-arrow-up-s-fill"></i>' : '<i class="ri-arrow-down-s-fill"></i>'} ${Math.abs(val12m).toFixed(2)}%`;
        val12mEl.className = `market-strip-value ${val12m >= 0 ? 'text-green' : 'text-red'}`;

        const valMes = data.mercado.valorizacao_mes || 0;
        const valMesEl = document.getElementById('strip_val_mes');
        valMesEl.innerText = `${valMes > 0 ? '+' : ''}${valMes.toFixed(2)}%`;
        valMesEl.className = valMes >= 0 ? 'text-green fw-bold' : 'text-red fw-bold';
    }

    // --- Header ---
    const nameEl = document.getElementById('display_name');
    const logoImg = document.getElementById('asset_logo');
    const logoPlaceholder = document.getElementById('asset_icon_placeholder');
    
    if (nameEl) nameEl.innerText = toTitleCase(data.meta.empresa);

    // Setor e Indústria
    const badges = document.getElementById('asset_badges_container');
    if (badges) {
      badges.style.display = 'flex';
      document.getElementById('display_sector').innerText = data.meta.setor || 'N/A';
      document.getElementById('display_industry').innerText = data.meta.industria || 'N/A';
    }

    // --- Valuation Cards ---
    const v = data.valuation;
    updateCard('P/L', v['P/L'], false);
    updateCard('P/VP', v['P/VP'], false);
    updateCard('EV/EBITDA', v['EV_Ebitda'], false);
    updateCard('LPA', v['LPA'], false);
    updateCard('VPA', v['VPA'], false);
    updateCard('Beta (5Y)', v['beta'], false);
    updateCard('PEG Ratio', v['peg_ratio'], false);

    // Logo Logic (Prioridade Total para Icones B3 em BR Stocks)
    if (logoImg && requestedTicker) {
        const fullTicker = requestedTicker.toUpperCase();
        const cleanTicker = fullTicker.split(".")[0];
        let logoUrl = null;

        // 1. Mapeamento Direto (AAPL, Indices, Crypto)
        if (ASSET_LOGOS[fullTicker]) {
            logoUrl = ASSET_LOGOS[fullTicker];
        } 
        // 2. Icones B3 (Repositorio Oficial - Melhor para BR)
        else {
            logoUrl = `https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/${cleanTicker}.png`;
        }

        logoImg.src = logoUrl;
        logoImg.onload = () => {
          logoImg.style.display = "block";
          if (logoPlaceholder) logoPlaceholder.style.display = "none";
        };

        logoImg.onerror = () => {
          // Se falhou o B3 ou Direto, tenta Clearbit via Website
          if (data.meta.website && data.meta.website !== 'N/A') {
              try {
                  const domain = new URL(data.meta.website).hostname.replace('www.', '');
                  logoImg.src = `https://logo.clearbit.com/${domain}`;
                  // Se o Clearbit carregar agora, o erro de antes é resolvido.
                  // Mas precisamos garantir que ele não entre em loop se o Clearbit também falhar.
                  logoImg.onerror = () => {
                      logoImg.src = `https://www.google.com/s2/favicons?domain=${data.meta.website}&sz=128`;
                      logoImg.onerror = () => {
                        logoImg.style.display = "none";
                        if (logoPlaceholder) logoPlaceholder.style.display = "block";
                      };
                  };
              } catch(e) {
                  logoImg.style.display = "none";
                  if (logoPlaceholder) logoPlaceholder.style.display = "block";
              }
          } else {
              logoImg.style.display = "none";
              if (logoPlaceholder) logoPlaceholder.style.display = "block";
          }
        };
    }
    
    const priceBlock = document.getElementById('price-header');
    if (priceBlock) priceBlock.style.visibility = 'visible';
    
    const currentPrice = data.price;
    if (currentPrice) {
        const priceEl = document.querySelector('.current-price');
        if (priceEl) priceEl.innerText = currentPrice.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    }
    
    // --- Metric Cards ---
    // (Consolidado na parte superior)
    // Mercado e Risco Removido (Subiu para Market Strip)

    updateCard('Dív. Liq / EBITDA', data.endividamento['DivLiq_Ebitda'], false);
    updateCard('Liquidez Corr.', data.endividamento['Liq_Corrente'], false);
    updateCard('Dívida Bruta', data.endividamento['Div_Bruta'], false, true);
    updateCard('Disponibilidades', data.raw.disponibilidades, false, true);
    
    updateCard('Margem Bruta', data.eficiencia['Margem_Bruta'], true);
    updateCard('Margem Líquida', data.eficiencia['Margem_Liquida'], true);
    updateCard('ROE', data.eficiencia['ROE'], true);
    updateCard('ROIC', data.eficiencia['ROIC'], true);

    // Sumário
    const descEl = document.getElementById('display_description');
    if (descEl) descEl.innerText = data.meta.descricao || "Descrição não disponível.";
    
    const webEl = document.getElementById('display_website');
    if (webEl && data.meta.website && data.meta.website !== 'N/A') {
        webEl.href = data.meta.website;
        webEl.style.display = 'inline-block';
    }

    // --- Heatmap ---
    applyHeatmapRules(data);

    // --- Charts ---
    renderDividendChart(data.proventos);

    // --- News ---
    const newsContainer = document.getElementById('news-container');
    const newsTitle = document.getElementById('news-section-title');
    
    if (newsContainer && newsTitle) {
        newsContainer.innerHTML = ''; // Clear previous
        
        if (data.news && data.news.length > 0) {
            newsTitle.style.display = 'flex';
            newsContainer.style.display = 'flex'; // row-cards is usually flex or grid

            data.news.forEach(item => {
                const col = document.createElement('div');
                col.className = 'col-sm-6 col-md-3'; // 4 cards per row on large screens
                
                col.innerHTML = `
                    <a href="${item.link}" target="_blank" class="news-card">
                        <img src="${item.thumbnail}" class="news-thumb" alt="News Image" onerror="this.src='https://placehold.co/600x400/1e1e24/FFF?text=No+Image'">
                        <div class="news-content">
                            <div class="news-meta">
                                <span class="news-publisher">${item.publisher}</span>
                                <span>${item.published}</span>
                            </div>
                            <h5 class="news-title">${item.title}</h5>
                        </div>
                    </a>
                `;
                newsContainer.appendChild(col);
            });
        } else {
            // Show discrete message if no news
            newsTitle.style.display = 'flex';
            newsContainer.style.display = 'block';
            newsContainer.innerHTML = '<div class="text-secondary small fst-italic mt-2">Nenhuma notícia recente encontrada para este ativo.</div>';
        }
    }
}

function renderDividendChart(proventos) {
    if (!proventos || proventos.length === 0) return;

    const options = {
        series: [{
            name: 'Dividendos Pagos',
            data: proventos.map(i => i.total_pago)
        }],
        chart: {
            type: 'bar',
            height: '100%',
            toolbar: { show: false },
            background: 'transparent'
        },
        colors: ['#00E396'],
        plotOptions: {
            bar: {
                borderRadius: 4,
                columnWidth: '50%',
            }
        },
        dataLabels: { enabled: false },
        xaxis: {
            categories: proventos.map(i => i.ano),
            axisBorder: { show: false },
            labels: { style: { colors: '#a1a1aa' } }
        },
        yaxis: {
            labels: { style: { colors: '#a1a1aa' }, formatter: (v) => `R$ ${v.toFixed(2)}` }
        },
        grid: { borderColor: '#27272a', strokeDashArray: 4 },
        tooltip: {
            theme: 'dark',
            y: { formatter: (v) => `R$ ${v.toFixed(2)}` }
        }
    };

    if (dividendChart) dividendChart.destroy();
    dividendChart = new ApexCharts(document.querySelector("#chart-proventos"), options);
    dividendChart.render();
}

function updateCard(label, value, isPercent, isCurrency = false) {
    const cards = Array.from(document.querySelectorAll('.metric-card'));
    const target = cards.find(c => {
        const text = c.querySelector('.metric-label').innerText.toUpperCase();
        return text.includes(label.toUpperCase()) || text === label.toUpperCase();
    });
    
    if (target) {
        const valEl = target.querySelector('.metric-value');
        if (value === '-' || value === undefined || value === 0) {
            // Se for 0 em moeda/perc, pode ser dado real, mas se for '-' é nulo
            if (value === 0 && (isPercent || isCurrency)) {
               // keep going
            } else if (value !== 0) {
               valEl.innerText = '-';
               return;
            }
        }
        
        if (isCurrency && typeof value === 'number') {
            valEl.innerText = formatCurrency(value);
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
    return `R$ ${val.toLocaleString('pt-BR')}`;
}

function applyHeatmapRules(data) {
    const colorize = (label, conditionGood, conditionBad) => {
        const cards = Array.from(document.querySelectorAll('.metric-card'));
        const target = cards.find(c => c.querySelector('.metric-label').innerText.toUpperCase().includes(label.toUpperCase()));
        if (!target) return;
        
        const bar = target.querySelector('.quality-bar');
        bar.className = 'quality-bar';
        target.classList.remove('positive', 'negative');
        
        let val = null;
        if (label === 'P/L') val = data.valuation['P/L'];
        if (label === 'ROE') val = data.eficiencia['ROE'];
        if (label === 'Margem Líquida') val = data.eficiencia['Margem_Liquida'];
        if (label === 'Dív. Liq / EBITDA') val = data.endividamento['DivLiq_Ebitda'];

        if (val !== null && val !== undefined && val !== '-') {
             if (conditionGood(val)) {
                 bar.classList.add('qb-good');
                 target.classList.add('positive');
             } else if (conditionBad(val)) {
                 bar.classList.add('qb-bad');
                 target.classList.add('negative');
             } else {
                 bar.classList.add('qb-neutral');
             }
        }
    };

    colorize('P/L', v => v > 0 && v < 15, v => v < 0 || v > 30);
    colorize('ROE', v => v > 15, v => v < 5);
    colorize('Margem Líquida', v => v > 10, v => v < 2);
    colorize('Dív. Liq / EBITDA', v => v < 2.5, v => v > 3.5);
}

function toTitleCase(str) {
    if (!str) return '';
    return str.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());
}
