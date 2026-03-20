'use strict';

class TTLCache {
  constructor(ttlMs = 5 * 60 * 1000) {
    this._ttlMs = ttlMs;
    this._store = new Map();
  }

  set(key, value) {
    this._store.set(key, { value, ts: Date.now() });
  }

  get(key) {
    const entry = this._store.get(key);
    if (!entry) return null;
    if (Date.now() - entry.ts > this._ttlMs) {
      this._store.delete(key);
      return null;
    }
    return entry.value;
  }

  has(key) {
    return this.get(key) !== null;
  }

  clear() {
    this._store.clear();
  }

  // 만료된 항목 전체 정리
  purgeExpired() {
    const now = Date.now();
    for (const [key, entry] of this._store) {
      if (now - entry.ts > this._ttlMs) this._store.delete(key);
    }
  }
}

const instance = new TTLCache(5 * 60 * 1000);
// 5분마다 만료 항목 자동 정리 (메모리 누수 방지)
setInterval(() => instance.purgeExpired(), 5 * 60 * 1000).unref();

module.exports = instance;
