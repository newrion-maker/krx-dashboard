document.addEventListener('DOMContentLoaded', async () => {
    // 로컬 파일 시스템에서 직접 열 경우(file://) CORS 정책으로 인해 fetch가 실패할 수 있습니다.
    // 이를 방지하기 위한 샘플 데이터 폴백 로직을 추가합니다.
    const mockData = {
        "date": "2026년 04월 21일 (화)",
        "generated_at": "13:30 (샘플)",
        "summary": {
            "total_amount": 29120350309487, "total_str": "29.1조",
            "theme_amount": 11366418341054, "theme_str": "11.4조",
            "theme_ratio": 39.0, "sector_count": 2, "theme_count": 2, "top60_count": 60
        },
        "sectors": [
            {
                "sector": "AI/로봇", "total_amount": 4921150722866, "total_str": "4.9조",
                "themes": [
                    {
                        "theme": "온디바이스 AI", "total_amount": 4921150722866, "total_str": "4.9조", "count": 3,
                        "champion": { "ticker": "000660", "name": "SK하이닉스", "change": 4.97, "amount_str": "4.3조" },
                        "stocks": [
                            { "ticker": "080220", "name": "제주반도체", "change": 8.95, "amount_str": "4,567억" }
                        ]
                    }
                ]
            },
            {
                "sector": "전기차/미래차", "total_amount": 802767438523, "total_str": "8,027억",
                "themes": [
                    {
                        "theme": "자동차 대표주", "total_amount": 802767438523, "total_str": "8,027억", "count": 3,
                        "champion": { "ticker": "005380", "name": "현대차", "change": 3.61, "amount_str": "5,112억" },
                        "stocks": [
                            { "ticker": "012330", "name": "현대모비스", "change": 6.43, "amount_str": "1,461억" }
                        ]
                    }
                ]
            }
        ],
        "top60": [
            { "ticker": "000660", "name": "SK하이닉스", "close": 1224000, "change": 4.97, "amount_str": "4.3조", "market": "KOSPI", "sector_name": "AI/로봇", "theme_name": "온디바이스 AI" }
        ]
    };

    let data;
    try {
        // 캐시 방지를 위해 타임스탬프 추가
        const response = await fetch('data.json?t=' + new Date().getTime());
        if (!response.ok) throw new Error('Data not found');
        data = await response.json();
    } catch (error) {
        console.warn('Using mock data due to fetch error (likely local file access):', error);
        data = mockData;
    }
    
    renderHeader(data);
    renderSummary(data);
    renderSectors(data);
    renderThemesWithSectors(data);
    renderTop60(data.top60);
    setupTabs();
});

function renderHeader(data) {
    const el = document.getElementById('header-date');
    if (!el) return;
    el.querySelector('.date').textContent = data.date;
    el.querySelector('.time').textContent = `분석 일시: ${data.generated_at}`;
}

function renderSummary(data) {
    const s = data.summary;
    document.getElementById('total-amount').textContent = s.total_str;
    document.getElementById('top60-count').textContent = `${s.top60_count}개 종목 분석`;
    
    document.getElementById('theme-ratio').textContent = `${s.theme_ratio}%`;
    document.getElementById('theme-amount').textContent = `주도 비중: ${s.theme_str}`;
    document.getElementById('theme-count').textContent = `${s.theme_count}개 테마`;
    
    const secLabel = document.getElementById('sector-count-label');
    if (secLabel) secLabel.textContent = `${s.sector_count}개 주도 섹터 발견`;

    // Animate Gauge
    const circle = document.getElementById('ratio-circle');
    if (circle) {
        circle.setAttribute('stroke-dasharray', `${s.theme_ratio}, 100`);
    }
}

function renderSectors(data) {
    const container = document.getElementById('sector-container');
    if (!container) return;
    container.innerHTML = '';
    
    const sectors = data.sectors || [];
    const totalMarketAmount = data.summary.total_amount;
    
    sectors.forEach((sec, index) => {
        const shareRatio = ((sec.total_amount / totalMarketAmount) * 100).toFixed(1);
        const card = document.createElement('div');
        card.className = 'sector-item-card fade-in';
        card.style.animationDelay = `${0.2 + (index * 0.05)}s`;
        
        card.innerHTML = `
            <div class="sector-info-top">
                <span class="sector-name-label">${sec.sector}</span>
                <span class="sector-value-label">${sec.total_str} (${shareRatio}%)</span>
            </div>
            <div class="sector-progress-bg">
                <div class="sector-progress-fill" style="width: ${shareRatio}%"></div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderThemesWithSectors(data) {
    const container = document.getElementById('theme-container');
    if (!container) return;
    container.innerHTML = '';
    
    const sectors = data.sectors || [];
    const totalMarketAmount = data.summary.total_amount;

    sectors.forEach((sec, sIdx) => {
        const secGroup = document.createElement('div');
        secGroup.className = 'sector-group-container fade-in';
        secGroup.style.animationDelay = `${0.3 + (sIdx * 0.1)}s`;
        
        secGroup.innerHTML = `
            <div class="sector-group-header">
                <h3>${sec.sector}</h3>
                <span class="sector-group-badge">${sec.themes.length}개 테마</span>
                <span style="font-size: 0.85rem; color: var(--text-dim);">합계 ${sec.total_str}</span>
            </div>
            <div class="theme-grid"></div>
        `;
        
        const grid = secGroup.querySelector('.theme-grid');
        
        sec.themes.forEach((t, tIdx) => {
            const card = document.createElement('div');
            card.className = 'theme-card';
            
            const shareRatio = ((t.total_amount / totalMarketAmount) * 100).toFixed(1);
            
            const stocksHtml = t.stocks.map(s => `
                <li class="stock-item">
                    <div class="stock-name-grp">
                        <span class="stock-name">${s.name}</span>
                        <span class="stock-ticker mobile-hide-detail">${s.ticker}</span>
                    </div>
                    <div class="stock-values">
                        <div class="${s.change > 0 ? 'change-up' : 'change-down'}">${s.change > 0 ? '+' : ''}${s.change}%</div>
                        <div style="font-size: 0.75rem; color: var(--text-dim);">${s.amount_str}</div>
                    </div>
                </li>
            `).join('');

            card.innerHTML = `
                <div class="theme-header">
                    <div class="theme-title-grp">
                        <span class="theme-name">${t.theme}</span>
                        <div class="theme-stats">
                            <span class="stat-item">거래: <strong>${t.total_str}</strong></span>
                            <span class="stat-item">비중: <strong>${shareRatio}%</strong></span>
                        </div>
                    </div>
                </div>
                <div class="theme-content">
                    <div class="champion">
                        <div class="champ-icon">👑</div>
                        <div class="champ-info">
                            <div class="champ-name">${t.champion.name}</div>
                            <div class="champ-amount">${t.champion.amount_str}</div>
                        </div>
                        <div class="champ-change">${t.champion.change > 0 ? '+' : ''}${t.champion.change}%</div>
                    </div>
                    <ul class="stock-list">
                        ${stocksHtml}
                    </ul>
                </div>
            `;
            grid.appendChild(card);
        });
        
        container.appendChild(secGroup);
    });
}

function renderTop60(stocks) {
    const tbody = document.getElementById('top60-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    stocks.forEach((s, index) => {
        const tr = document.createElement('tr');
        tr.className = 'fade-in';
        
        // 섹터/테마 정보 표시
        let categoryHtml = '-';
        if (s.sector_name) {
            categoryHtml = `<div style="font-weight: 600; font-size: 0.85rem;">${s.sector_name}</div>
                            <div style="font-size: 0.7rem; color: var(--text-dim);">${s.theme_name}</div>`;
        } else if (s.sector) {
            const secStr = typeof s.sector === 'string' ? s.sector : s.sector.sector;
            categoryHtml = `<div style="font-weight: 600; font-size: 0.85rem;">${secStr}</div>`;
        }

        tr.innerHTML = `
            <td style="color: var(--text-dim); font-weight: bold;">#${index + 1}</td>
            <td>
                <div style="font-weight: 700;">${s.name}</div>
                <div class="mobile-hide-detail" style="font-size: 0.75rem; color: var(--text-dim);">${s.ticker} / ${s.market}</div>
            </td>
            <td><div class="category-tag">${categoryHtml}</div></td>
            <td>${s.close.toLocaleString()}원</td>
            <td class="${s.change > 0 ? 'change-up' : s.change < 0 ? 'change-down' : ''}" style="font-weight: 700;">
                ${s.change > 0 ? '+' : ''}${s.change}%
            </td>
            <td style="font-weight: 600;">${s.amount_str}</td>
        `;
        tbody.appendChild(tr);
    });
}

function setupTabs() {
    const btns = document.querySelectorAll('.tab-btn');
    const themesView = document.getElementById('themes-view');
    const top60View = document.getElementById('top60-view');

    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.getAttribute('data-tab');
            if (tab === 'themes') {
                themesView.style.display = 'block';
                top60View.style.display = 'none';
            } else {
                themesView.style.display = 'none';
                top60View.style.display = 'block';
            }
        });
    });
}
