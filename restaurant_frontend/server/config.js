'use strict';

require('dotenv').config();

module.exports = {
  PORT:                   process.env.PORT || 3000,
  GOOGLE_PLACES_API_KEY:  process.env.GOOGLE_PLACES_API_KEY || '',
  KAKAO_REST_API_KEY:     process.env.KAKAO_REST_API_KEY || '',
  CORS_ORIGIN:            process.env.CORS_ORIGIN || 'http://localhost:5500',
};
