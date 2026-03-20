'use strict';

const { searchNearbyRestaurants } = require('./googlePlaces');
const { searchLocalRestaurants }  = require('./kakaoLocal');

const EARTH_RADIUS_KM = 6371;

function haversine(lat1, lng1, lat2, lng2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const dLat  = toRad(lat2 - lat1);
  const dLng  = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2
          + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(a));
}

function normalizeName(name) {
  return name.toLowerCase().replace(/[\s\-_.,·]/g, '');
}

function areDuplicates(nameA, nameB) {
  const a = normalizeName(nameA);
  const b = normalizeName(nameB);
  if (!a || !b) return false;
  return a.includes(b) || b.includes(a);
}

function mergeIntoGoogle(googleEntry, naverEntry) {
  const merged = { ...googleEntry };
  if (!merged.platforms.includes('naver')) {
    merged.platforms = [...merged.platforms, 'naver'];
  }
  if (!merged.desc && naverEntry.desc)             merged.desc = naverEntry.desc;
  if (merged.sub.length <= 1 && naverEntry.sub.length > 1) merged.sub = naverEntry.sub;
  return merged;
}

/**
 * Merge and deduplicate results from Google and Naver.
 */
function mergeRestaurants(googleResults, naverResults) {
  const merged = [...googleResults];

  for (const naver of naverResults) {
    let matched = false;
    for (let gi = 0; gi < merged.length; gi++) {
      if (areDuplicates(merged[gi].name, naver.name)) {
        merged[gi] = mergeIntoGoogle(merged[gi], naver);
        matched = true;
        break;
      }
    }
    if (!matched) merged.push(naver);
  }

  return merged.map((restaurant, index) => ({ ...restaurant, id: index + 1 }));
}

/**
 * Add `dist` field (km, 1 decimal) and filter out entries without coordinates.
 */
function calculateDistances(restaurants, userLat, userLng) {
  return restaurants
    .map((r) => {
      const lat = r._lat  != null ? r._lat  : r._mapy;
      const lng = r._lng  != null ? r._lng  : r._mapx;
      if (lat == null || lng == null) return null;
      return { ...r, dist: Math.round(haversine(userLat, userLng, lat, lng) * 10) / 10 };
    })
    .filter(Boolean);
}

const CATEGORY_QUERY_MAP = {
  korean:   '한식',
  japanese: '일식',
  chinese:  '중식',
  western:  '양식',
  hot:      '국밥',    // '국물요리' → 카카오에서 실제 검색되는 단어로 변경
  cold:     '냉면',    // '냉요리' → '냉면'
  spicy:    '마라탕',  // '매운음식' → '마라탕'
};

/**
 * Fetch from both APIs, merge, filter by radius, and sort by distance.
 * subs가 있으면 각 서브태그를 카카오 검색 쿼리로 사용해 더 정확한 결과를 반환.
 */
async function fetchAndMergeRestaurants(lat, lng, radiusKm, category, subs) {
  const radiusMeters = radiusKm * 1000;

  // subs가 있으면 서브태그 키워드로 검색, 없으면 카테고리 쿼리 사용
  const kakaoQueries = (subs && subs.length > 0)
    ? subs.flatMap((s) => s.split('/').map((p) => p.trim()).filter(Boolean))  // '찌개/탕' → ['찌개', '탕']
    : [category ? (CATEGORY_QUERY_MAP[category] || '맛집') : '맛집'];

  let googleResults  = [];
  let kakaoResultArrays = [];

  try {
    [googleResults, ...kakaoResultArrays] = await Promise.all([
      searchNearbyRestaurants(lat, lng, radiusMeters),
      ...kakaoQueries.map((q) => searchLocalRestaurants(q, lat, lng, radiusMeters)),
    ]);
  } catch (err) {
    console.error('[dataMerger] fetchAndMergeRestaurants error:', err.message);
  }

  // 카카오 결과 중복 제거 후 합치기
  const seenIds     = new Set();
  const kakaoResults = [];
  for (const arr of kakaoResultArrays) {
    for (const item of arr) {
      if (!seenIds.has(item.id)) {
        seenIds.add(item.id);
        kakaoResults.push({ ...item, category: category || item.category });
      }
    }
  }

  const merged      = mergeRestaurants(googleResults, kakaoResults);
  const withDist    = calculateDistances(merged, lat, lng);
  const inRadius    = withDist.filter((r) => r.dist <= radiusKm);
  inRadius.sort((a, b) => a.dist - b.dist);

  // Strip internal coordinate fields
  return inRadius.map(({ _lat, _lng, _mapx, _mapy, _address, ...rest }) => rest);
}

module.exports = { mergeRestaurants, calculateDistances, fetchAndMergeRestaurants };
