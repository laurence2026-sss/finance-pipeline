'use strict';

const https  = require('https');
const config = require('../config');
const cache  = require('./cache');

const GOOGLE_API_KEY = config.GOOGLE_PLACES_API_KEY;

const TYPE_TO_CATEGORY = {
  korean_restaurant:        'korean',
  japanese_restaurant:      'japanese',
  chinese_restaurant:       'chinese',
  american_restaurant:      'western',
  italian_restaurant:       'western',
  french_restaurant:        'western',
  mexican_restaurant:       'western',
  mediterranean_restaurant: 'western',
  seafood_restaurant:       'korean',
  ramen_restaurant:         'japanese',
  sushi_restaurant:         'japanese',
};

const TYPE_TO_KOREAN_TAG = {
  korean_restaurant:        '한식',
  japanese_restaurant:      '일식',
  chinese_restaurant:       '중식',
  american_restaurant:      '양식',
  italian_restaurant:       '이탈리안',
  french_restaurant:        '프렌치',
  mexican_restaurant:       '멕시칸',
  mediterranean_restaurant: '지중해식',
  seafood_restaurant:       '해산물',
  ramen_restaurant:         '라멘',
  sushi_restaurant:         '스시',
  fast_food_restaurant:     '패스트푸드',
  cafe:                     '카페',
  bakery:                   '베이커리',
  bar:                      '주점',
  restaurant:               '식당',
};

const PRICE_LEVEL_MAP = {
  PRICE_LEVEL_FREE:          '무료',
  PRICE_LEVEL_INEXPENSIVE:   '~10,000원대',
  PRICE_LEVEL_MODERATE:      '~20,000원대',
  PRICE_LEVEL_EXPENSIVE:     '~40,000원대',
  PRICE_LEVEL_VERY_EXPENSIVE:'40,000원 이상',
};

function httpsPost(url, body, headers) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify(body);
    const urlObj  = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      path:     urlObj.pathname + urlObj.search,
      method:   'POST',
      headers: {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(payload),
        ...headers,
      },
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
    req.write(payload);
    req.end();
  });
}

function normalizeGooglePlace(place) {
  const types = place.types || [];

  let category = 'western';
  for (const t of types) {
    if (TYPE_TO_CATEGORY[t]) { category = TYPE_TO_CATEGORY[t]; break; }
  }

  const sub = [...new Set(
    types.filter((t) => TYPE_TO_KOREAN_TAG[t]).map((t) => TYPE_TO_KOREAN_TAG[t])
  )];

  const price = PRICE_LEVEL_MAP[place.priceLevel] || null;

  // SECURITY: Do NOT embed the API key in the URL that is returned to clients.
  // Instead, return a server-side proxy path. The actual Google photo URL
  // (including the key) is built server-side inside the /api/photos proxy route.
  let img = null;
  if (place.photos && place.photos.length > 0) {
    const photoRef = encodeURIComponent(place.photos[0].name);
    img = `/api/photos?ref=${photoRef}`;
  }

  return {
    id:        `google_${place.id}`,
    name:      place.displayName ? place.displayName.text : '알 수 없음',
    category,
    sub:       sub.length > 0 ? sub : ['식당'],
    dist:      null,
    rating:    place.rating || null,
    price,
    desc:      (place.editorialSummary && place.editorialSummary.text) || '',
    platforms: ['google'],
    img,
    _lat:      place.location ? place.location.latitude  : null,
    _lng:      place.location ? place.location.longitude : null,
  };
}

async function searchNearbyRestaurants(lat, lng, radiusMeters) {
  const cacheKey = `google_${lat}_${lng}_${radiusMeters}`;
  if (cache.has(cacheKey)) return cache.get(cacheKey);

  try {
    const body = {
      includedTypes: ['restaurant'],
      maxResultCount: 20,
      locationRestriction: {
        circle: {
          center: { latitude: lat, longitude: lng },
          radius: radiusMeters,
        },
      },
    };

    const headers = {
      'X-Goog-Api-Key':  GOOGLE_API_KEY,
      'X-Goog-FieldMask': 'places.id,places.displayName,places.rating,places.userRatingCount,places.priceLevel,places.photos,places.types,places.location,places.editorialSummary',
    };

    const response = await httpsPost(
      'https://places.googleapis.com/v1/places:searchNearby',
      body,
      headers
    );

    const results = (response.places || []).map(normalizeGooglePlace);
    cache.set(cacheKey, results);
    return results;
  } catch (err) {
    console.error('[googlePlaces] searchNearbyRestaurants error:', err.message);
    return [];
  }
}

module.exports = { searchNearbyRestaurants, normalizeGooglePlace };
