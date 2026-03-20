'use strict';

const express                        = require('express');
const { fetchAndMergeRestaurants }   = require('../services/dataMerger');

const router = express.Router();

const VALID_CATEGORIES = new Set([
  'korean', 'japanese', 'chinese', 'western', 'hot', 'cold', 'spicy',
]);

/**
 * GET /api/restaurants
 * Query params:
 *   lat      {float}  required  - 사용자 위도
 *   lng      {float}  required  - 사용자 경도
 *   radius   {float}  optional  - 검색 반경 km (기본 1.0, 최소 0.1, 최대 5.0)
 *   category {string} optional  - 카테고리 필터
 *   subs     {string} optional  - 쉼표구분 서브태그 필터 (OR)
 */
router.get('/', async (req, res) => {
  const { lat, lng, radius, category, subs } = req.query;

  if (lat === undefined || lng === undefined) {
    return res.status(400).json({ success: false, error: 'lat and lng query parameters are required.' });
  }

  const parsedLat = parseFloat(lat);
  const parsedLng = parseFloat(lng);

  if (isNaN(parsedLat) || isNaN(parsedLng)) {
    return res.status(400).json({ success: false, error: 'lat and lng must be valid numbers.' });
  }
  if (parsedLat < -90  || parsedLat > 90)   return res.status(400).json({ success: false, error: 'lat must be between -90 and 90.' });
  if (parsedLng < -180 || parsedLng > 180)  return res.status(400).json({ success: false, error: 'lng must be between -180 and 180.' });

  const parsedRadius = radius !== undefined ? parseFloat(radius) : 1.0;
  if (isNaN(parsedRadius) || parsedRadius < 0.1 || parsedRadius > 5.0) {
    return res.status(400).json({ success: false, error: 'radius must be a number between 0.1 and 5.0.' });
  }

  const categoryFilter = category && typeof category === 'string' ? category.trim() : null;
  const subsFilter     = subs && typeof subs === 'string'
    ? subs.split(',').map((s) => s.trim()).filter(Boolean)
    : [];

  if (categoryFilter && !VALID_CATEGORIES.has(categoryFilter)) {
    return res.status(400).json({
      success: false,
      error: `Invalid category. Must be one of: ${[...VALID_CATEGORIES].join(', ')}.`,
    });
  }

  try {
    const data = await fetchAndMergeRestaurants(parsedLat, parsedLng, parsedRadius, categoryFilter, subsFilter);
    return res.json({ success: true, count: data.length, data });
  } catch (err) {
    console.error('[GET /api/restaurants] error:', err);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

module.exports = router;
