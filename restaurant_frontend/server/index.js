'use strict';

const express       = require('express');
const path          = require('path');
const helmet        = require('helmet');
const cors          = require('cors');
const https         = require('https');
const rateLimit     = require('express-rate-limit');
const { PORT, CORS_ORIGIN, GOOGLE_PLACES_API_KEY } = require('./config');
const restaurantsRouter     = require('./routes/restaurants');
const { restaurantsLimiter } = require('./middleware/rateLimiter');

const app = express();

// --- Security middleware: helmet with explicit Content Security Policy ---
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc:  ["'self'"],
      scriptSrc:   ["'self'"],
      styleSrc:    ["'self'", "'unsafe-inline'"],
      imgSrc:      ["'self'", 'data:', 'https://images.unsplash.com'],
      connectSrc:  ["'self'", 'http://localhost:3000'],
      fontSrc:     ["'self'"],
      objectSrc:   ["'none'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
}));

// --- CORS: only allow the configured origin; never fall back to '*' ---
// If CORS_ORIGIN is not set in the environment, default to localhost only.
const resolvedCorsOrigin = CORS_ORIGIN || 'http://localhost:5500';

app.use(cors({
  origin:               resolvedCorsOrigin,
  methods:              ['GET'],
  optionsSuccessStatus: 200,
}));

// Explicit pre-flight OPTIONS handling so browsers always receive CORS headers
app.options('*', cors({
  origin:               resolvedCorsOrigin,
  methods:              ['GET'],
  optionsSuccessStatus: 200,
}));

// --- Body parsing ---
app.use(express.json());

// --- Global rate limiter: 100 requests per 15 minutes per IP ---
const globalLimiter = rateLimit({
  windowMs:        15 * 60 * 1000,
  max:             100,
  standardHeaders: true,
  legacyHeaders:   false,
  message:         { success: false, error: 'Too many requests. Please try again later.' },
});
app.use(globalLimiter);

// --- Routes ---
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

// Stricter per-route limiter (20 req/min) applied before the restaurants router
// to guard against external API cost-amplification attacks.
app.use('/api/restaurants', restaurantsLimiter, restaurantsRouter);

/**
 * GET /api/photos?ref={encodedPhotoName}
 *
 * Server-side proxy for Google Places photo media.
 * The Google API key is NEVER exposed to the frontend; it is appended here,
 * on the server, and the response is streamed back to the client.
 */
app.get('/api/photos', (req, res) => {
  const { ref } = req.query;

  if (!ref || typeof ref !== 'string') {
    return res.status(400).json({ success: false, error: 'Missing or invalid ref parameter.' });
  }

  // Basic allowlist: photo names returned by the Places API follow the pattern
  // "places/{placeId}/photos/{photoId}" with only alphanumeric chars, dashes,
  // underscores and forward slashes.
  const decodedRef = decodeURIComponent(ref);
  if (!/^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/.test(decodedRef)) {
    return res.status(400).json({ success: false, error: 'Invalid photo reference format.' });
  }

  if (!GOOGLE_PLACES_API_KEY) {
    return res.status(503).json({ success: false, error: 'Photo service unavailable.' });
  }

  const googleUrl = `https://places.googleapis.com/v1/${decodedRef}/media?maxWidthPx=300&key=${GOOGLE_PLACES_API_KEY}`;
  const urlObj    = new URL(googleUrl);

  const options = {
    hostname: urlObj.hostname,
    path:     urlObj.pathname + urlObj.search,
    method:   'GET',
    headers:  { 'Accept': 'image/*' },
  };

  const proxyReq = https.request(options, (proxyRes) => {
    // Only proxy image responses; reject anything unexpected
    const contentType = proxyRes.headers['content-type'] || '';
    if (!contentType.startsWith('image/')) {
      res.status(502).json({ success: false, error: 'Upstream returned non-image content.' });
      proxyRes.resume(); // drain the response
      return;
    }

    res.setHeader('Content-Type', contentType);
    res.setHeader('Cache-Control', 'public, max-age=86400'); // cache for 1 day
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[/api/photos] proxy error:', err.message);
    if (!res.headersSent) {
      res.status(502).json({ success: false, error: 'Failed to fetch photo.' });
    }
  });

  proxyReq.end();
});

// --- 정적 파일 서빙 (프론트엔드) ---
const frontendPath = path.join(__dirname, '..');
app.use(express.static(frontendPath));
app.get('/', (_req, res) => {
  res.sendFile(path.join(frontendPath, 'index.html'));
});

// --- 404 handler ---
app.use((_req, res) => {
  res.status(404).json({ success: false, error: 'Route not found.' });
});

// --- Global error handler ---
// Deliberately sanitized: stack traces and internal details are logged server-side
// only and are never forwarded to the client.
app.use((err, _req, res, _next) => {
  console.error('[Unhandled error]', err);
  res.status(500).json({ success: false, error: 'Internal server error.' });
});

// --- Start server ---
app.listen(PORT, () => {
  console.log(`PickEat API Server running on port ${PORT}`);
});

module.exports = app;
