'use strict';

const path     = require('path');
const fs       = require('fs');
const Database = require('better-sqlite3');

const DB_PATH     = path.join(__dirname, 'pickeat.db');
const SCHEMA_PATH = path.join(__dirname, 'schema.sql');

const db = new Database(DB_PATH);

// WAL mode for better concurrent read performance
db.pragma('journal_mode = WAL');

// Execute schema on startup
const schema = fs.readFileSync(SCHEMA_PATH, 'utf8');
db.exec(schema);

/**
 * Haversine formula — returns distance in km between two lat/lng points.
 */
function haversine(lat1, lon1, lat2, lon2) {
  const R    = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a    = Math.sin(dLat / 2) ** 2
             + Math.cos(lat1 * Math.PI / 180)
             * Math.cos(lat2 * Math.PI / 180)
             * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/**
 * Fetch restaurants filtered by location, radius, category, and sub-tags.
 *
 * @param {number}   lat      - User latitude
 * @param {number}   lng      - User longitude
 * @param {number}   radiusKm - Search radius in km
 * @param {string}   category - Optional category filter (exact match)
 * @param {string[]} subs     - Optional sub-tag filter (OR logic)
 * @returns {object[]} Array of restaurant objects with `dist` field
 */
function getRestaurants(lat, lng, radiusKm, category, subs) {
  let query  = 'SELECT * FROM restaurants';
  const params = [];

  if (category) {
    // SECURITY NOTE: `category` is passed as a bound parameter (?) in a
    // prepared statement — NOT via string interpolation. better-sqlite3
    // parameterized queries are safe from SQL injection. The value is also
    // pre-validated against the VALID_CATEGORIES whitelist in the route
    // handler before reaching this function, providing defence-in-depth.
    query += ' WHERE category = ?';
    params.push(category);
  }

  const rows = db.prepare(query).all(...params);

  return rows
    .map((row) => {
      const distKm = haversine(lat, lng, row.lat, row.lng);
      return { ...row, _distKm: distKm };
    })
    .filter((row) => row._distKm <= radiusKm)
    .filter((row) => {
      if (!subs || subs.length === 0) return true;
      const rowSubs = JSON.parse(row.sub || '[]');
      return subs.some((s) => rowSubs.includes(s));
    })
    .sort((a, b) => a._distKm - b._distKm)
    .map(({ _distKm, ...rest }) => ({
      id:        rest.id,
      name:      rest.name,
      category:  rest.category,
      sub:       JSON.parse(rest.sub       || '[]'),
      dist:      Math.round(_distKm * 10) / 10,
      rating:    rest.rating,
      price:     rest.price,
      desc:      rest.description,
      platforms: JSON.parse(rest.platforms || '[]'),
      img:       rest.img || null,
    }));
}

module.exports = { db, getRestaurants };
