'use strict';

const https  = require('https');
const config = require('../config');
const cache  = require('./cache');

const NAVER_CLIENT_ID     = config.NAVER_CLIENT_ID;
const NAVER_CLIENT_SECRET = config.NAVER_CLIENT_SECRET;

const KOREAN_QUERY_TO_CATEGORY = {
  '한식':   'korean',
  '일식':   'japanese',
  '중식':   'chinese',
  '양식':   'western',
  '국물요리': 'hot',
  '냉요리':  'cold',
  '매운음식': 'spicy',
  '맛집':   'korean',
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
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error(`JSON parse error: ${e.message}`)); }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

function stripHtml(str) {
  return str ? str.replace(/<\/?b>/g, '').replace(/<[^>]+>/g, '') : '';
}

function deriveCategory(query) {
  return KOREAN_QUERY_TO_CATEGORY[query] || 'korean';
}

function normalizeNaverPlace(item, queryCategory) {
  const sub = (item.category || '')
    .split('>')
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    id:        `naver_${item.link}`,
    name:      stripHtml(item.title),
    category:  queryCategory,
    sub:       sub.length > 0 ? sub : ['식당'],
    dist:      null,
    rating:    null,
    price:     null,
    desc:      item.description || '',
    platforms: ['naver'],
    img:       null,
    _address:  item.roadAddress || item.address || '',
    _mapx:     item.mapx ? parseInt(item.mapx, 10) / 10000000 : null,
    _mapy:     item.mapy ? parseInt(item.mapy, 10) / 10000000 : null,
  };
}

async function searchLocalRestaurants(query, lat, lng) {
  const cacheKey = `naver_${query}_${lat}_${lng}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  try {
    const encodedQuery = encodeURIComponent(query);
    const url = `https://openapi.naver.com/v1/search/local.json?query=${encodedQuery}&display=20&sort=random`;

    const headers = {
      'X-Naver-Client-Id':     NAVER_CLIENT_ID,
      'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
    };

    const response = await httpsGet(url, headers);
    const queryCategory = deriveCategory(query);
    const results = (response.items || []).map((item) => normalizeNaverPlace(item, queryCategory));

    cache.set(cacheKey, results);
    return results;
  } catch (err) {
    console.error('[naverLocal] searchLocalRestaurants error:', err.message);
    return [];
  }
}

module.exports = { searchLocalRestaurants, normalizeNaverPlace };
