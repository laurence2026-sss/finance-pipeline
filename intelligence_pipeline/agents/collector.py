"""
Agent 1: Collector (수집 에이전트)
===================================
모든 소스에서 Raw Data를 수집하고 통합합니다.
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    RSS_FEEDS, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_SUBREDDITS, REDDIT_POST_LIMIT, REDDIT_SORT,
    WATCHLIST_TICKERS, VOLUME_SPIKE_THRESHOLD, DATA_DIR
)
from sources.rss_feeds import collect_rss_feeds
from sources.reddit_client import RedditCollector
from sources.finance_data import collect_finance_data


def run_collector() -> List[Dict]:
    """
    모든 Tier 1~2 소스에서 데이터를 수집하고 통합합니다.
    
    Returns:
        통합된 Raw Intelligence 리스트
    """
    print("=" * 60)
    print(f"🌐 Agent 1 (Collector) 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_items = []
    
    # 1) RSS 피드 수집
    print("\n📡 [1/3] RSS 피드 수집 중...")
    rss_items = collect_rss_feeds(RSS_FEEDS)
    all_items.extend(rss_items)
    
    # 2) Reddit 수집
    print("\n📡 [2/3] Reddit 수집 중...")
    reddit = RedditCollector(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    reddit_items = reddit.collect(REDDIT_SUBREDDITS, limit=REDDIT_POST_LIMIT, sort=REDDIT_SORT)
    all_items.extend(reddit_items)
    
    # 3) Yahoo Finance 수집
    print("\n📡 [3/3] Yahoo Finance 스캔 중...")
    finance_items = collect_finance_data(WATCHLIST_TICKERS, VOLUME_SPIKE_THRESHOLD)
    all_items.extend(finance_items)
    
    # 중복 제거 (ID 기준)
    seen_ids = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_items.append(item)
    
    # 결과 저장
    output_path = os.path.join(DATA_DIR, "raw_intelligence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(unique_items, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Agent 1 완료: 총 {len(unique_items)}건 수집 → {output_path}")
    return unique_items


if __name__ == "__main__":
    items = run_collector()
    print(f"\n--- 수집 결과 상위 5건 ---")
    for item in items[:5]:
        print(f"[{item['source']}] {item['title']}")
