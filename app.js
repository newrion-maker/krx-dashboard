document.addEventListener('DOMContentLoaded', async () => {
    // 로컬 파일 시스템에서 직접 열 경우(file://) CORS 정책으로 인해 fetch가 실패할 수 있습니다.
    // 이를 방지하기 위한 샘플 데이터 폴백 로직을 추가합니다.
    const mockData = {
        "date": "2026년 04월 20일 (월)",
        "generated_at": "17:00",
        "summary": {
            "total_amount": 226000000000000, "total_str": "22.6조",
            "theme_amount": 120000000000000, "theme_str": "12.0조",
            "theme_ratio": 53.3, "theme_count": 6, "top60_count": 60
        },
        "themes": [
            {
                "theme": "전기전자", "total_amount": 70000000000000, "total_str": "7.0조", "count": 8,
                "champion": { "ticker": "000660", "name": "SK하이닉스", "change": 3.37, "amount": 44000000000000, "amount_str": "4.4조" },
                "stocks": [
                    { "ticker": "005930", "name": "삼성전자", "change": 1.25, "amount": 15000000000000, "amount_str": "1.5조" },
                    { "ticker": "066570", "name": "LG전자", "change": 2.1, "amount": 5000000000000, "amount_str": "5000억" }
                ]
            },
            {
                "theme": "반도체", "total_amount": 13000000000000, "total_str": "1.3조", "count": 5,
                "champion": { "ticker": "041510", "name": "주성엔지니어링", "change": 29.97, "amount": 5000000000000, "amount_str": "5000억" },
                "stocks": [
                    { "ticker": "067310", "name": "하나마이크론", "change": 5.4, "amount": 2000000000000, "amount_str": "2000억" }
                ]
            }
        ],
        "top60": [
            { "ticker": "000660", "name": "SK하이닉스", "close": 180000, "change": 3.37, "amount": 44000000000000, "amount_str": "4.4조", "market": "KOSPI", "sector": "전기전자" },
            { "ticker": "005930", "name": "삼성전자", "close": 82000, "change": 1.25, "amount": 15000000000000, "amount_str": "1.5조", "market": "KOSPI", "sector": "전기전자" }
        ]
    };

    let data;
    try {
        const response = await fetch('data.json');
        if (!response.ok) throw new Error('Data not found');
        data = await response.json();
    } catch (error) {
        console.warn('Using mock data due to fetch error (likely local file access):', error);
        data = mockData;
    }
    
    renderHeader(data);
    renderSummary(data);
    renderThemes(data);
    renderTop60(data.top60);
    setupTabs();
});

function renderHeader(data) {
    const el = document.getElementById('header-date');
    el.querySelector('.date').textContent = data.date;
    el.querySelector('.time').textContent = `분석 일시: ${data.generated_at}`;
}

function renderSummary(data) {
    const s = data.summary;
    document.getElementById('total-amount').textContent = s.total_str;
    document.getElementById('top60-count').textContent = `${s.top60_count}개 종목 분석`;
    
    document.getElementById('theme-ratio').textContent = `${s.theme_ratio}%`;
    document.getElementById('theme-amount').textContent = `주도 업종: ${s.theme_str}`;
    document.getElementById('theme-count').textContent = `${s.theme_count}개`;

    // Animate Gauge
    const circle = document.getElementById('ratio-circle');
    if (circle) {
        circle.setAttribute('stroke-dasharray', `${s.theme_ratio}, 100`);
    }
}

function renderThemes(data) {
    const container = document.getElementById('theme-container');
    container.innerHTML = '';
    const themes = data.themes;
    const totalTop60Amount = data.summary.total_amount;

    themes.forEach((t, index) => {
        const card = document.createElement('div');
        card.className = 'theme-card fade-in';
        card.style.animationDelay = `${0.3 + (index * 0.1)}s`;
        
        const shareRatio = ((t.total_amount / totalTop60Amount) * 100).toFixed(1);
        
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
                        <span class="stat-item">거래대금: <strong>${t.total_str}</strong></span>
                        <span class="stat-item">비중: <strong>${shareRatio}%</strong></span>
                    </div>
                </div>
                <span class="theme-count">${t.count}개 종목</span>
            </div>
            <div class="theme-content">
                <div class="champion">
                    <div class="champ-icon">👑</div>
                    <div class="champ-info">
                        <div class="champ-name">
                            ${t.champion.name} 
                            <small class="mobile-hide-detail" style="font-size: 0.65rem; color: var(--text-dim);">${t.champion.ticker}</small>
                        </div>
                        <div class="champ-amount" style="font-size: 0.75rem; color: var(--text-dim);">거래대금 ${t.champion.amount_str}</div>
                    </div>
                    <div class="champ-change">${t.champion.change > 0 ? '+' : ''}${t.champion.change}%</div>
                </div>
                <ul class="stock-list">
                    ${stocksHtml}
                </ul>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderTop60(stocks) {
    const tbody = document.getElementById('top60-body');
    tbody.innerHTML = '';

    stocks.forEach((s, index) => {
        const tr = document.createElement('tr');
        tr.className = 'fade-in';
        tr.innerHTML = `
            <td style="color: var(--text-dim); font-weight: bold;">#${index + 1}</td>
            <td>
                <div style="font-weight: 700;">${s.name}</div>
                <div class="mobile-hide-detail" style="font-size: 0.75rem; color: var(--text-dim);">${s.ticker} / ${s.market}</div>
            </td>
            <td><span style="background: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px; font-size: 0.8rem;">${s.sector}</span></td>
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
