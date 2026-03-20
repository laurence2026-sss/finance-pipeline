"""
Agent 3: Validator (한국 반영 검증 에이전트)
=============================================
필터 통과된 정보가 이미 한국 뉴스에 나왔는지 확인합니다.
네이버 뉴스 검색 API를 사용하며, API 키 없으면 폴백 로직 사용.
"""

import json
import os
import re
import requests
from datetime import datetime
from typing import List, Dict
from urllib.parse import quote

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET,
    NAVER_NEWS_API_URL, KOREA_REFLECTED_THRESHOLD, DATA_DIR
)

# 영어 키워드 → 한국어 검색어 매핑 (자주 등장하는 금융/테크 용어)
KEYWORD_MAP = {
    "nvidia": "엔비디아",
    "photonics": "포토닉스 OR 광학",
    "silicon photonics": "실리콘 포토닉스",
    "liquid cooling": "액체냉각 OR 수냉",
    "smr": "소형모듈원전 OR SMR",
    "rate cut": "금리인하",
    "rate hike": "금리인상",
    "fed": "연준 OR 연방준비제도",
    "recession": "경기침체",
    "semiconductor": "반도체",
    "data center": "데이터센터",
    "ai chip": "AI칩 OR AI반도체",
    "bitcoin": "비트코인",
    "ethereum": "이더리움",
    "tsmc": "TSMC OR 대만반도체",
    "samsung": "삼성전자",
    "sk hynix": "SK하이닉스",
    "coherent": "코히런트 OR COHR",
    "fabrinet": "파브리넷",
    "lumentum": "루멘텀",
    "acquisition": "인수합병",
    "ipo": "IPO OR 상장",
    "layoffs": "감원 OR 해고 OR 구조조정",
    "crash": "폭락",
    "surge": "급등",
    "rocket lab": "로켓랩",
    "space": "우주항공 OR 우주산업",
    "satellite": "위성",
    "broadcom": "브로드컴",
    "arm": "ARM",
    "hbm": "HBM OR 고대역폭메모리",
    "robotics": "로보틱스",
    "redwire": "레드와이어",
    "blacksky": "블랙스카이",
    "tesla": "테슬라",
    "teradyne": "테라다인",
    "optimus": "옵티머스",
    "robot os": "로봇OS",
    "humanoid": "휴머노이드",
}


def run_validator(filtered_items: List[Dict] = None) -> List[Dict]:
    """
    필터 통과된 정보가 한국 뉴스에 반영되었는지 확인합니다.
    
    - 🔥 독점 정보: 한국 뉴스 0~2건 → 아직 한국에 안 알려진 정보
    - ⚡ 초기 반영: 한국 뉴스 3~5건 → 막 뉴스가 나오기 시작한 정보
    - ⚪ 이미 반영: 한국 뉴스 6건 이상 → 이미 다 아는 정보
    """
    print("=" * 60)
    print(f"🇰🇷 Agent 3 (Validator) 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 필터링된 데이터 로드
    if filtered_items is None:
        filtered_path = os.path.join(DATA_DIR, "filtered_intelligence.json")
        if not os.path.exists(filtered_path):
            print("[Validator] filtered_intelligence.json 없음 — Filter를 먼저 실행하세요")
            return []
        with open(filtered_path, "r", encoding="utf-8") as f:
            filtered_items = json.load(f)
    
    print(f"  입력: {len(filtered_items)}건")
    
    results = []
    for item in filtered_items:
        # 제목에서 핵심 키워드 추출
        search_query = _extract_korean_query(item)
        
        if not search_query:
            item["korea_status"] = "⚡ 검증 불가"
            item["korea_news_count"] = -1
            item["korea_search_query"] = ""
            results.append(item)
            continue
        
        # 네이버 뉴스 검색
        news_count = _search_naver_news(search_query)
        
        # 태그 결정
        if news_count < 0:
            status = "⚡ 검증 불가"
        elif news_count < KOREA_REFLECTED_THRESHOLD:
            status = "🔥 독점 정보"
        elif news_count < KOREA_REFLECTED_THRESHOLD * 2:
            status = "⚡ 초기 반영"
        else:
            status = "⚪ 이미 반영"
        
        item["korea_status"] = status
        item["korea_news_count"] = news_count
        item["korea_search_query"] = search_query
        results.append(item)
        
        print(f"  {status} [{news_count}건] {item['title'][:50]}...")
    
    # 최종 결과 저장
    output_path = os.path.join(DATA_DIR, "final_intelligence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    exclusive = sum(1 for r in results if "독점" in r.get("korea_status", ""))
    early = sum(1 for r in results if "초기" in r.get("korea_status", ""))
    reflected = sum(1 for r in results if "이미" in r.get("korea_status", ""))
    
    print(f"\n✅ Agent 3 완료:")
    print(f"  🔥 독점 정보: {exclusive}건")
    print(f"  ⚡ 초기 반영: {early}건")
    print(f"  ⚪ 이미 반영: {reflected}건")
    print(f"  → 저장: {output_path}")
    
    return results


def _extract_korean_query(item: Dict) -> str:
    """영문 제목에서 한국어 검색 키워드를 추출합니다."""
    title = item.get("title", "").lower()
    summary = item.get("summary", "").lower()
    text = title + " " + summary
    
    matched_queries = []
    for eng_keyword, kor_keyword in KEYWORD_MAP.items():
        if eng_keyword.lower() in text:
            matched_queries.append(kor_keyword)
    
    if matched_queries:
        return " ".join(matched_queries[:3])  # 최대 3개 키워드 조합
    
    # 매칭 안 되면 제목에서 고유명사 추출 시도
    words = re.findall(r'[A-Z][a-zA-Z]+', item.get("title", ""))
    proper_nouns = [w for w in words if len(w) > 3 and w not in ("The", "This", "That", "Just", "From", "With", "These", "Those", "About")]
    if proper_nouns:
        return proper_nouns[0]
    
    return ""


def _search_naver_news(query: str) -> int:
    """네이버 뉴스 검색 API로 한국 기사 수를 확인합니다."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        # API 키 없으면 웹 스크레이핑 폴백
        return _search_naver_fallback(query)
    
    try:
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        }
        params = {
            "query": query,
            "display": 10,
            "sort": "date",
        }
        resp = requests.get(NAVER_NEWS_API_URL, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("total", 0)
    except Exception as e:
        print(f"  [Validator] 네이버 API 실패 ({query}): {e}")
        return -1


def _search_naver_fallback(query: str) -> int:
    """네이버 API 키 없을 때 간이 웹 검색으로 대체"""
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=5)
        
        # 검색 결과 수 파싱 (근사값)
        match = re.search(r'총\s*(\d[\d,]*)\s*건', resp.text)
        if match:
            return int(match.group(1).replace(",", ""))
        
        # 결과 리스트가 있는지 체크
        news_count = resp.text.count('class="news_tit"')
        return news_count
    except:
        return -1


if __name__ == "__main__":
    items = run_validator()
    print(f"\n--- 최종 결과 (독점 정보만) ---")
    for item in items:
        if "독점" in item.get("korea_status", ""):
            print(f"🔥 [{item['source']}] {item['title']}")
            if item.get("summary_ko"):
                print(f"   → {item['summary_ko']}")
