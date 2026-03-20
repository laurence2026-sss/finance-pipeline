'use strict';

const rateLimit = require('express-rate-limit');

/**
 * Strict per-route rate limiter for /api/restaurants.
 *
 * Motivation: each request to /api/restaurants may trigger calls to the
 * Google Places API and the Naver Local API, both of which incur real monetary
 * costs. A tighter limit (20 req / 1 min per IP) caps the maximum cost an
 * individual client can generate, protecting against both accidental
 * hammering and deliberate cost-amplification attacks.
 */
const restaurantsLimiter = rateLimit({
  windowMs:        60 * 1000,  // 1 minute window
  max:             20,          // max 20 requests per IP per window
  standardHeaders: true,
  legacyHeaders:   false,
  message: {
    success: false,
    error:   'Too many restaurant search requests. Please wait a moment and try again.',
  },
});

module.exports = { restaurantsLimiter };
