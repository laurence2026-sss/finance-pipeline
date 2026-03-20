/* ============================================================
   Global Intelligence Pipeline — Dashboard App
   실시간 데이터 패칭 + UI 렌더링
   ============================================================ */

const API_BASE = window.location.origin;
let allItems = [];
let currentFilter = 'all';
let pollInterval = null;

// ============================================================
// 초기화
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    // 15초마다 자동 새로고침
    pollInterval = setInterval(loadData, 15000);
});

// ============================================================
// 데이터 로드
// ============================================================
async function loadData() {
    try {
        const [intelRes, metaRes] = await Promise.all([
            fetch(`${API_BASE}/api/intelligence`),
            fetch(`${API_BASE}/api/meta`),
        ]);

        const intelData = await intelRes.json();
        const metaData = await metaRes.json();

        if (intelData.items && intelData.items.length > 0) {
            allItems = intelData.items;
            renderCards(allItems);
        }

        if (metaData.last_run) {
            updateStats(metaData);
        }
    } catch (e) {
        console.log('데이터 로드 대기 중...');
    }
}

// ============================================================
// 통계 업데이트
// ============================================================
function updateStats(meta) {
    setText('statRaw', meta.raw_count || 0);
    setText('statFiltered', meta.filtered_count || 0);
    setText('statExclusive', meta.exclusive_count || 0);
    setText('statEarly', meta.early_count || 0);
    setText('statReflected', meta.reflected_count || 0);
    setText('statElapsed', meta.elapsed_seconds ? `${meta.elapsed_seconds}s` : '—');

    // 마지막 실행 시간
    if (meta.last_run) {
        const d = new Date(meta.last_run);
        setText('lastRunTime', d.toLocaleString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }

    // 상태 표시 업데이트
    const dot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    dot.className = 'status-dot';
    statusText.textContent = `${meta.final_count || 0}건 감시 중`;
}

// ============================================================
// 카드 렌더링
// ============================================================
function renderCards(items) {
    const feed = document.getElementById('feed');
    const emptyState = document.getElementById('emptyState');

    // 필터 적용
    let filtered = items;
    if (currentFilter === 'exclusive') {
        filtered = items.filter(i => (i.korea_status || '').includes('독점'));
    } else if (currentFilter === 'early') {
        filtered = items.filter(i => (i.korea_status || '').includes('초기'));
    } else if (currentFilter === 'reflected') {
        filtered = items.filter(i => (i.korea_status || '').includes('이미'));
    }

    if (filtered.length === 0) {
        feed.innerHTML = '';
        if (emptyState) feed.appendChild(emptyState);
        return;
    }

    feed.innerHTML = filtered.map((item, idx) => createCard(item, idx)).join('');
}

function createCard(item, index) {
    const status = item.korea_status || '';
    let statusClass = '';
    let badgeClass = '';
    let badgeText = '';

    if (status.includes('독점')) {
        statusClass = 'exclusive';
        badgeClass = 'badge-exclusive';
        badgeText = '🔥 독점 정보';
    } else if (status.includes('초기')) {
        statusClass = 'early';
        badgeClass = 'badge-early';
        badgeText = '⚡ 초기 반영';
    } else if (status.includes('이미')) {
        statusClass = 'reflected';
        badgeClass = 'badge-reflected';
        badgeText = '⚪ 이미 반영';
    }

    const score = item.filter_score || 0;
    const tickers = (item.related_tickers || [])
        .map(t => `<span class="ticker">${t}</span>`)
        .join('');

    const time = item.published_at
        ? new Date(item.published_at).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        : '';

    const summary = item.summary_ko || item.summary || '';
    const koreaQuery = item.korea_search_query ? `검색: "${item.korea_search_query}" (${item.korea_news_count}건)` : '';

    return `
        <div class="intel-card ${statusClass}" style="animation-delay: ${index * 0.05}s"
             onclick="window.open('${item.url || '#'}', '_blank')">
            <div class="card-top">
                <div class="card-badges">
                    ${badgeText ? `<span class="badge ${badgeClass}">${badgeText}</span>` : ''}
                    <span class="badge badge-score">${score}점</span>
                    <span class="badge badge-source">${item.source || ''}</span>
                </div>
                <span class="card-time">${time}</span>
            </div>
            <div class="card-title">${escapeHtml(item.title || '')}</div>
            ${summary ? `<div class="card-summary">${escapeHtml(summary.substring(0, 200))}</div>` : ''}
            <div class="card-footer">
                <div class="card-tickers">${tickers}</div>
                <span class="card-korea-query">${escapeHtml(koreaQuery)}</span>
            </div>
        </div>
    `;
}

// ============================================================
// 필터 탭
// ============================================================
function filterCards(filter, btnEl) {
    currentFilter = filter;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    renderCards(allItems);
}

// ============================================================
// 파이프라인 실행
// ============================================================
async function triggerPipeline() {
    const btn = document.getElementById('btnRun');
    btn.classList.add('running');
    btn.innerHTML = '<span class="btn-icon">⟳</span> 실행 중...';

    // 상태 표시
    const dot = document.querySelector('.status-dot');
    dot.className = 'status-dot running';
    document.querySelector('.status-text').textContent = '파이프라인 실행 중...';

    try {
        await fetch(`${API_BASE}/api/run`, { method: 'POST' });
        addLog('🚀 파이프라인 실행 시작', 'agent1');

        // 실행 완료 대기 (폴링)
        let attempts = 0;
        const checkDone = setInterval(async () => {
            attempts++;
            try {
                const res = await fetch(`${API_BASE}/api/meta`);
                const meta = await res.json();
                if (meta.final_count !== undefined) {
                    updateStats(meta);
                    await loadData();
                    addLog(`✅ 완료: ${meta.exclusive_count}건 독점 정보 발견`, 'agent3');
                }
            } catch (e) { /* 아직 실행 중 */ }

            if (attempts > 60) { // 최대 5분 대기
                clearInterval(checkDone);
                resetButton();
            }
        }, 5000);

        // 30초 후 버튼 복구 (백그라운드 실행이므로)
        setTimeout(() => {
            resetButton();
        }, 30000);

    } catch (e) {
        addLog(`❌ 실행 실패: ${e.message}`, 'agent1');
        resetButton();
    }
}

function resetButton() {
    const btn = document.getElementById('btnRun');
    btn.classList.remove('running');
    btn.innerHTML = '<span class="btn-icon">▶</span> 파이프라인 실행';
    const dot = document.querySelector('.status-dot');
    dot.className = 'status-dot';
}

// ============================================================
// 로그 패널
// ============================================================
function toggleLog() {
    document.getElementById('logPanel').classList.toggle('open');
}

function addLog(message, agentClass = '') {
    const content = document.getElementById('logContent');
    const time = new Date().toLocaleTimeString('ko-KR');
    const entry = document.createElement('div');
    entry.className = `log-entry ${agentClass}`;
    entry.textContent = `[${time}] ${message}`;
    content.prepend(entry);
}

// ============================================================
// 유틸
// ============================================================
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
