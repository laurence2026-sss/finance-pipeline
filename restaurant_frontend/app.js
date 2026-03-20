// 데이터 구조와 상태 (App Logic)
const menuData = {
    'korean': { name: '한식', icon: '🍲', subs: ['국밥', '찌개/탕', '고기구이', '비빔밥', '백반'] },
    'japanese': { name: '일식', icon: '🍣', subs: ['초밥', '라멘', '돈카츠', '덮밥', '우동'] },
    'chinese': { name: '중식', icon: '🍜', subs: ['짜장/짬뽕', '마라탕', '딤섬', '양꼬치'] },
    'western': { name: '양식', icon: '🍝', subs: ['파스타', '스테이크', '피자', '햄버거'] },
    'hot': { name: '따뜻한 국물', icon: '♨️', subs: ['전골', '쌀국수', '우동/라멘', '국밥'] },
    'cold': { name: '시원한 요리', icon: '❄️', subs: ['냉면', '모밀', '밀면', '샐러드'] },
    'spicy': { name: '매운 요리', icon: '🌶️', subs: ['마라탕', '떡볶이', '매운갈비찜', '낙지볶음'] },
};

// --- 백엔드 API 설정 ---
const API_BASE_URL = 'http://localhost:3000';

// 사용자 위치 (Geolocation API로 획득 후 업데이트)
let userLocation = { lat: 37.498, lng: 127.028 }; // 기본값: 서울 강남구 역삼동

let state = { distance: 1.0, mainCategory: null, selectedSubs: new Set(), isLoading: false };

/**
 * 백엔드 API에서 식당 데이터를 가져오는 비동기 함수.
 * @param {number} lat       - 사용자 위도
 * @param {number} lng       - 사용자 경도
 * @param {number} distance  - 검색 반경 (km)
 * @param {string} [category] - 카테고리 필터 (선택)
 * @param {string[]} [subs]  - 서브태그 필터 배열 (선택)
 * @returns {Promise<Object[]>} 식당 데이터 배열
 */
async function fetchRestaurants(lat, lng, distance, category, subs) {
    const params = new URLSearchParams({
        lat:    lat.toString(),
        lng:    lng.toString(),
        radius: distance.toString(),
    });
    if (category)              params.set('category', category);
    if (subs && subs.length)   params.set('subs', subs.join(','));

    const response = await fetch(`${API_BASE_URL}/api/restaurants?${params}`);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `서버 오류 (${response.status})`);
    }
    const json = await response.json();
    return json.data || [];
}

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initLocation();
    renderMainCategories();
    setupEventListeners();
    renderRestaurants();
});

// Geolocation API로 실제 사용자 위치 획득
function requestUserLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            userLocation.lat = pos.coords.latitude;
            userLocation.lng = pos.coords.longitude;
            document.getElementById('current-location').innerText = '현재 위치';
            renderRestaurants();
        },
        () => {
            // 권한 거부 시 기본 위치(강남구) 유지
            console.warn('[PickEat] 위치 접근 거부 — 기본 위치(강남구)로 진행합니다.');
        },
        { timeout: 5000 }
    );
}

function initClock() {
    setInterval(() => {
        document.getElementById('current-time').innerText = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    }, 1000);
}

function initLocation() {
    document.getElementById('current-location').innerText = "서울 강남구 역삼동";
    requestUserLocation(); // 실제 위치 권한 요청
}

// 3. 게슈탈트 원칙: 액션 칩 클래스(.action-chip) 적용
function renderMainCategories() {
    const container = document.getElementById('main-categories');
    container.innerHTML = '';
    
    Object.entries(menuData).forEach(([key, data]) => {
        const div = document.createElement('div');
        div.className = 'action-chip main-tag'; 
        div.dataset.key = key;
        div.innerHTML = `${data.icon} ${data.name}`;
        
        div.addEventListener('click', () => {
            document.querySelectorAll('.main-tag').forEach(t => t.classList.remove('active'));
            
            if (state.mainCategory === key) {
                state.mainCategory = null; state.selectedSubs.clear();
                document.getElementById('sub-category-container').style.display = 'none';
            } else {
                div.classList.add('active'); state.mainCategory = key; state.selectedSubs.clear();
                renderSubCategories(key);
            }
            renderRestaurants();
        });
        container.appendChild(div);
    });
}

function renderSubCategories(mainKey) {
    const container = document.getElementById('sub-category-container');
    const subsContainer = document.getElementById('sub-categories');
    subsContainer.innerHTML = '';
    
    menuData[mainKey].subs.forEach(sub => {
        const div = document.createElement('div');
        div.className = 'action-chip sub-tag';
        div.innerText = sub;
        
        div.addEventListener('click', () => {
            if (state.selectedSubs.has(sub)) { state.selectedSubs.delete(sub); div.classList.remove('active'); } 
            else { state.selectedSubs.add(sub); div.classList.add('active'); }
            renderRestaurants();
        });
        subsContainer.appendChild(div);
    });
    container.style.display = 'block';
}

function setupEventListeners() {
    const slider = document.getElementById('distance-slider');
    slider.addEventListener('input', (e) => {
        state.distance = parseFloat(e.target.value);
        document.getElementById('distance-value').innerText = state.distance.toFixed(1);
    });
    slider.addEventListener('change', renderRestaurants);
    document.getElementById('btn-search').addEventListener('click', renderRestaurants);
    document.getElementById('btn-random').addEventListener('click', handleRandomPick);
}

// 필터링은 이제 서버에서 처리 — 이 함수는 API 호출 래퍼로 대체됨
async function getFilteredRestaurants() {
    const subs = Array.from(state.selectedSubs);
    return fetchRestaurants(
        userLocation.lat,
        userLocation.lng,
        state.distance,
        state.mainCategory || undefined,
        subs.length ? subs : undefined
    );
}

function createCardHTML(rest) {
    // 플랫폼 뱃지 (접근성: 흑백 투명화 .platform-icon)
    const pBadges = rest.platforms.map(p => `<span class="platform-icon">${p === 'naver' ? 'N' : 'G'}</span>`).join('');
    
    // 정보 태그 (게슈탈트: 칩과 구분되는 .info-tag)
    const tagsHtml = rest.sub.map(t => `<span class="info-tag">#${t}</span>`).join('');
    
    // 썸네일 처리 (이미지 있으면 삽입, 없으면 빈 공간 둚)
    const styleAttr = rest.img ? `style="background-image: url('${rest.img}');"` : '';
    const thClass = rest.img ? 'card-thumbnail has-img' : 'card-thumbnail';

    return `
        <!-- 사진과 메인 정보를 수평 배치 -->
        <div class="card-top-content">
            <div class="${thClass}" ${styleAttr}></div>
            <div class="card-info">
                <div class="card-header-main">
                    <div class="card-title">${rest.name} <div style="display:flex; gap:4px; margin-left:6px;">${pBadges}</div></div>
                    ${rest.rating != null ? `<div class="rating"><i class="fas fa-star"></i> ${rest.rating}</div>` : ''}
                </div>
                <div class="card-meta">
                    <div class="meta-row">
                        <span class="distance"><i class="fas fa-location-arrow"></i> ${rest.dist}km</span>
                    </div>
                    ${rest.price != null ? `<div class="meta-row"><span class="price-tag"><i class="fas fa-wallet" style="margin-right:4px;"></i>${rest.price}</span></div>` : ''}
                </div>
            </div>
        </div>
        
        <div class="card-tags">${tagsHtml}</div>
        
        <div class="card-desc">
            ${rest.desc}
        </div>
        
        <div class="card-actions">
            <!-- 사용자 기기에 네이버지도가 있으면 앱으로, 없으면 브라우저 네이버 지도로 바로 식당 검색 결과를 띄워주는 URL 규칙 -->
            <a href="https://map.naver.com/v5/search/${encodeURIComponent(rest.name)}" target="_blank" class="nav-btn">
                <i class="fas fa-map-signs"></i> 네이버 지도로 길찾기
            </a>
        </div>
    `;
}

async function renderRestaurants() {
    if (state.isLoading) return;
    state.isLoading = true;

    const list     = document.getElementById('restaurant-list');
    const countEl  = document.getElementById('results-count');
    const titleEl  = document.getElementById('results-title');

    // 로딩 상태 표시
    list.innerHTML = `<div style="text-align:center; padding: 40px 0; color: var(--text-muted);"><i class="fas fa-spinner fa-spin" style="font-size:24px; color:var(--primary-color);"></i><p style="margin-top:12px;">맛집 불러오는 중...</p></div>`;
    countEl.innerText = '';

    if (state.mainCategory) {
        titleEl.innerHTML = `반경 ${state.distance}km 내 <span style="color:var(--primary-color)">${menuData[state.mainCategory].name}</span>`;
    } else {
        titleEl.innerText = `반경 ${state.distance}km 내 추천 리스트`;
    }

    let filtered = [];
    try {
        filtered = await getFilteredRestaurants();
    } catch (err) {
        console.error('[PickEat] API 호출 실패:', err.message);
        list.innerHTML = `<div style="text-align:center; padding: 40px 0; color: var(--text-muted);">서버에 연결할 수 없습니다.<br><small>${err.message}</small></div>`;
        countEl.innerText = '오류';
        state.isLoading = false;
        return;
    }

    state.isLoading = false;
    list.innerHTML  = '';
    countEl.innerText = `${filtered.length}곳 찾음`;

    if (filtered.length === 0) {
        list.innerHTML = `<div style="text-align:center; padding: 40px 0; color: var(--text-muted);">조건에 맞는 식당이 없습니다.</div>`;
        return;
    }

    filtered.forEach((rest, index) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.animationDelay = `${index * 0.05}s`;
        card.innerHTML = createCardHTML(rest);
        list.appendChild(card);
    });
}

async function handleRandomPick() {
    const loader = document.getElementById('random-loader');
    loader.classList.remove('hidden');

    let filtered = [];
    try {
        filtered = await getFilteredRestaurants();
    } catch (err) {
        loader.classList.add('hidden');
        alert(`서버 오류: ${err.message}`);
        return;
    }

    setTimeout(() => {
        loader.classList.add('hidden');

        if (filtered.length === 0) { alert("조건에 맞는 식당이 없습니다."); return; }

        const winner = filtered[Math.floor(Math.random() * filtered.length)];

        const list = document.getElementById('restaurant-list');
        list.innerHTML = '';
        document.getElementById('results-title').innerHTML = `<i class="fas fa-gift" style="color:var(--primary-color)"></i> 운명의 맛집`;
        document.getElementById('results-count').innerText = "1곳 당첨";

        const card = document.createElement('div');
        card.className = 'card';
        card.style.borderColor = 'var(--primary-color)';
        card.style.boxShadow   = '0 0 20px rgba(255,138,76,0.15)';
        card.innerHTML = createCardHTML(winner);
        list.appendChild(card);
    }, 1500);
}
