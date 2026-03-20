'use strict';

const https  = require('https');
const config = require('../config');
const cache  = require('./cache');

const KAKAO_REST_API_KEY = config.KAKAO_REST_API_KEY;

const CATEGORY_CODE_MAP = {
  korean:   'FD6',  // 음식점 (카카오는 대분류가 FD6 하나)
  japanese: 'FD6',
  chinese:  'FD6',
  western:  'FD6',
  hot:      'FD6',
  cold:     'FD6',
  spicy:    'FD6',
};

const QUERY_MAP = {
  korean:   '한식',
  japanese: '일식',
  chinese:  '중식',
  western:  '양식',
  hot:      '국물요리',
  cold:     '냉요리',
  spicy:    '매운음식',
};

function httpsGet(url, headers) {
  return new Promise((resolve, reject) => {
    const urlObj  = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      path:     urlObj.pathname + urlObj.search,
      method:   'GET',
      headers,
    };

    const req = https.request(options, (res) => {
      const chunks = [];
      res.on('data', (chunk) => { chunks.push(chunk); });
      res.on('end', () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
        catch (e) { reject(new Error(`JSON parse error: ${e.message}`)); }
      });
    });

    // 5초 타임아웃: 카카오 API 무응답 시 서버 먹통 방지
    req.setTimeout(5000, () => req.destroy(new Error('Kakao API timeout')));
    req.on('error', reject);
    req.end();
  });
}

function normalizeKakaoPlace(item, queryCategory) {
  const sub = (item.category_name || '')
    .split('>')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(1); // 첫 번째("음식점")는 제거

  return {
    id:        `kakao_${item.id}`,
    name:      item.place_name,
    category:  queryCategory,
    sub:       sub.length > 0 ? sub : ['식당'],
    dist:      item.distance ? Math.round(parseInt(item.distance, 10) / 100) / 10 : null, // m → km
    rating:    null,
    price:     null,
    desc:      item.road_address_name || item.address_name || '',
    platforms: ['naver'], // 프론트엔드 플랫폼 표시 호환용 (naver 배지 재활용)
    img:       null,
    _address:  item.road_address_name || item.address_name || '',
    _mapx:     parseFloat(item.x) || null, // 경도(lng)
    _mapy:     parseFloat(item.y) || null, // 위도(lat)
  };
}

/**
 * 카카오 키워드 장소 검색 API
 * https://developers.kakao.com/docs/latest/ko/local/dev-guide#search-by-keyword
 */
async function searchLocalRestaurants(query, lat, lng, radiusMeters = 2000) {
  // 좌표 소수점 4자리 반올림 → 캐시 히트율 향상 (11m 오차 이내는 같은 결과)
  const rLat = Math.round(lat * 10000) / 10000;
  const rLng = Math.round(lng * 10000) / 10000;
  const cacheKey = `kakao_${query}_${rLat}_${rLng}_${radiusMeters}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  try {
    const params = new URLSearchParams({
      query,
      x:          rLng.toString(),
      y:          rLat.toString(),
      radius:     Math.min(radiusMeters, 20000).toString(), // 최대 20km
      size:       '15',
      category_group_code: 'FD6',
    });

    const url = `https://dapi.kakao.com/v2/local/search/keyword.json?${params}`;
    const headers = { Authorization: `KakaoAK ${KAKAO_REST_API_KEY}` };

    const response = await httpsGet(url, headers);
    const queryCategory = Object.keys(QUERY_MAP).find((k) => QUERY_MAP[k] === query) || 'korean';
    const results = (response.documents || []).map((item) => normalizeKakaoPlace(item, queryCategory));

    cache.set(cacheKey, results);
    return results;
  } catch (err) {
    console.error('[kakaoLocal] searchLocalRestaurants error:', err.message);
    return [];
  }
}

module.exports = { searchLocalRestaurants, normalizeKakaoPlace };
