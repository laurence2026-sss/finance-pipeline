"""
RSS Feed Collector
==================
Tier 1 소스: RSS 피드에서 뉴스 헤드라인과 요약을 수집합니다.
ZeroHedge, SemiAnalysis, TrendForce, Hacker News 등.
"""

import feedparser
import hashlib
from datetime import datetime, timezone
from typing import List, Dict


def collect_rss_feeds(feeds: Dict[str, str]) -> List[Dict]:
    """
    여러 RSS 피드에서 최신 항목들을 수집합니다.
    
    Args:
        feeds: {피드_이름: 피드_URL} 딕셔너리
    
    Returns:
        수집된 뉴스 항목 리스트
    """
    results = []
    
    for source_name, feed_url in feeds.items():
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:  # 피드당 최대 10개
                # 고유 ID 생성 (중복 방지)
                raw_id = entry.get("link", "") + entry.get("title", "")
                item_id = hashlib.md5(raw_id.encode()).hexdigest()
                
                # 발행일 파싱
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_date = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
                else:
                    pub_date = datetime.now(timezone.utc).isoformat()
                
                item = {
                    "id": item_id,
                    "source": source_name,
                    "source_type": "rss",
                    "title": entry.get("title", "").strip(),
                    "summary": _clean_html(entry.get("summary", "")),
                    "url": entry.get("link", ""),
                    "published_at": pub_date,
                    "collected_at": datetime.now(timezone.utc).isoformat(),
                }
                results.append(item)
                
        except Exception as e:
            print(f"[RSS] {source_name} 수집 실패: {e}")
            continue
    
    print(f"[RSS] 총 {len(results)}건 수집 완료 ({len(feeds)}개 피드)")
    return results


def _clean_html(text: str) -> str:
    """HTML 태그 제거 및 텍스트 정제"""
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    clean = clean.replace("&#39;", "'").replace("&quot;", '"')
    return clean.strip()[:500]  # 최대 500자


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from config import RSS_FEEDS
    
    items = collect_rss_feeds(RSS_FEEDS)
    for item in items[:5]:
        print(f"\n[{item['source']}] {item['title']}")
        print(f"  요약: {item['summary'][:100]}...")
        print(f"  URL: {item['url']}")
