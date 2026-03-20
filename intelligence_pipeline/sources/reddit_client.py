"""
Reddit Client
==============
Tier 1 소스: Reddit API를 통해 핵심 서브레딧의 인기 포스트를 수집합니다.
r/wallstreetbets, r/stocks, r/semiconductor 등.
"""

import hashlib
import requests
from datetime import datetime, timezone
from typing import List, Dict


class RedditCollector:
    """Reddit API를 통해 서브레딧의 인기 포스트를 수집합니다."""
    
    BASE_URL = "https://oauth.reddit.com"
    AUTH_URL = "https://www.reddit.com/api/v1/access_token"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.headers = {"User-Agent": "IntelligencePipeline/1.0"}
    
    def _authenticate(self):
        """Reddit OAuth2 인증"""
        if not self.client_id or not self.client_secret:
            print("[Reddit] API 키 없음 — JSON 피드 폴백 사용")
            return False
        
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            data = {"grant_type": "client_credentials"}
            resp = requests.post(
                self.AUTH_URL, auth=auth, data=data,
                headers=self.headers, timeout=10
            )
            resp.raise_for_status()
            self.token = resp.json().get("access_token")
            self.headers["Authorization"] = f"Bearer {self.token}"
            return True
        except Exception as e:
            print(f"[Reddit] 인증 실패: {e}")
            return False
    
    def collect(self, subreddits: List[str], limit: int = 10, sort: str = "hot") -> List[Dict]:
        """
        여러 서브레딧에서 인기 포스트를 수집합니다.
        
        API 키가 없으면 JSON 피드(비인증)를 사용합니다.
        """
        use_api = self._authenticate()
        results = []
        
        for sub in subreddits:
            try:
                if use_api:
                    items = self._fetch_via_api(sub, limit, sort)
                else:
                    items = self._fetch_via_json(sub, limit, sort)
                results.extend(items)
            except Exception as e:
                print(f"[Reddit] r/{sub} 수집 실패: {e}")
                continue
        
        print(f"[Reddit] 총 {len(results)}건 수집 완료 ({len(subreddits)}개 서브레딧)")
        return results
    
    def _fetch_via_api(self, subreddit: str, limit: int, sort: str) -> List[Dict]:
        """OAuth API를 통한 수집"""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}"
        resp = requests.get(url, headers=self.headers, params={"limit": limit}, timeout=15)
        resp.raise_for_status()
        return self._parse_posts(resp.json(), subreddit)
    
    def _fetch_via_json(self, subreddit: str, limit: int, sort: str) -> List[Dict]:
        """비인증 JSON 피드를 통한 수집 (API 키 없을 때 폴백)"""
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return self._parse_posts(resp.json(), subreddit)
    
    def _parse_posts(self, data: dict, subreddit: str) -> List[Dict]:
        """Reddit API 응답을 파싱하여 표준 형식으로 변환"""
        items = []
        
        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            
            # 고유 ID
            raw_id = p.get("id", "") + p.get("title", "")
            item_id = hashlib.md5(raw_id.encode()).hexdigest()
            
            # 타임스탬프 변환
            created_utc = p.get("created_utc", 0)
            pub_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
            
            item = {
                "id": item_id,
                "source": f"r/{subreddit}",
                "source_type": "reddit",
                "title": p.get("title", "").strip(),
                "summary": (p.get("selftext", "") or "")[:500],
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "published_at": pub_date,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "upvote_ratio": p.get("upvote_ratio", 0),
                }
            }
            items.append(item)
        
        return items


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_SUBREDDITS
    
    collector = RedditCollector(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    items = collector.collect(REDDIT_SUBREDDITS[:2], limit=3)
    
    for item in items:
        print(f"\n[{item['source']}] {item['title']}")
        print(f"  점수: {item.get('metadata', {}).get('score', 0)}")
