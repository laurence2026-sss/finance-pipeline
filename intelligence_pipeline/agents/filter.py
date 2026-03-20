"""
Agent 2: Filter (노이즈 제거 에이전트)
========================================
우선순위:
  1) Groq (Llama 3.3 70B) - 무료/초고속
  2) Gemini 2.0 Flash (무료)
  3) GPT-4o mini (유료 폴백)
  4) 키워드 기반 (최후 폴백)
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# .env 파일 위치 (intelligence_pipeline/.env)
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(ENV_PATH)

from config import (
    OPENAI_API_KEY, FILTER_THRESHOLD,
    FILTER_SYSTEM_PROMPT, FILTER_MAX_TOKENS, DATA_DIR
)

# AI API 키들 로드
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 테마 키워드 (AI 없이 걸러낼 때 사용)
BIOTECH_KEYWORDS = [
    "FDA", "clinical trial", "Phase 1", "Phase 2", "Phase 3",
    "biotech", "pharmaceutical", "therapy", "drug approval", "IND",
    "NDA", "orphan drug", "biological", "biotech breakthrough",
    "rare disease", "longevity", "CRISPR", "GLP-1", "cancer therapy",
]

BATCH_SIZE = 8  # 한 번에 분석할 기사 수

def run_filter(raw_items: List[Dict] = None) -> List[Dict]:
    """
    수집된 정보를 필터링합니다.
    우선순위: Groq(Llama 3) -> Gemini -> OpenAI -> 키워드
    """
    print("=" * 60)
    print(f"🔍 Agent 2 (Filter) 시작 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if raw_items is None:
        raw_path = os.path.join(DATA_DIR, "raw_intelligence.json")
        if not os.path.exists(raw_path):
            print("[Filter] raw_intelligence.json 없음")
            return []
        with open(raw_path, "r", encoding="utf-8") as f:
            raw_items = json.load(f)

    print(f"  입력: {len(raw_items)}건")
    print(f"  Groq 키 상태: {'✅ 있음' if GROQ_API_KEY else '❌ 없음'}")
    print(f"  Gemini 키 상태: {'✅ 있음' if GEMINI_API_KEY else '❌ 없음'}")

    if GROQ_API_KEY:
        print("  모드: Groq (Llama 3.3 70B) 채점 (무료/초고속)")
        filtered = _filter_with_groq(raw_items)
    elif GEMINI_API_KEY:
        print("  모드: Gemini AI 채점")
        filtered = _filter_with_gemini(raw_items)
    elif OPENAI_API_KEY:
        print("  모드: GPT-4o mini AI 채점")
        filtered = _filter_with_gpt(raw_items)
    else:
        print("  모드: 키워드 기반 폴백 (API 키 없음)")
        filtered = _filter_with_keywords(raw_items)

    filtered.sort(key=lambda x: x.get("filter_score", 0), reverse=True)
    passed = [item for item in filtered if item.get("filter_score", 0) >= FILTER_THRESHOLD]

    output_path = os.path.join(DATA_DIR, "filtered_intelligence.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(passed, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Agent 2 완료: {len(raw_items)}건 → {len(passed)}건 통과")
    return passed

def _filter_with_groq(items: List[Dict]) -> List[Dict]:
    """Groq API를 사용한 배치 필터링"""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"  [Filter] Groq 라이브러리 에러: {e}")
        return _filter_with_keywords(items)

    results = []
    batches = [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

    for b_idx, batch in enumerate(batches):
        try:
            prompt = _build_batch_prompt(batch)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": FILTER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=FILTER_MAX_TOKENS * BATCH_SIZE
            )
            reply = chat_completion.choices[0].message.content.strip()
            batch = _parse_batch_response(reply, batch)
            print(f"  Groq 배치 {b_idx+1}/{len(batches)} 완료 ({len(batch)}건)")
        except Exception as e:
            print(f"  [Filter] Groq 배치 실패: {e}")
            for item in batch:
                item.setdefault("filter_score", 5)
        results.extend(batch)
    return results

def _filter_with_gemini(items: List[Dict]) -> List[Dict]:
    """Gemini Flash를 사용한 배치 AI 채점"""
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        return _filter_with_keywords(items)

    results = []
    batches = [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

    for b_idx, batch in enumerate(batches):
        try:
            prompt = _build_batch_prompt(batch)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=FILTER_SYSTEM_PROMPT,
                    temperature=0.1,
                )
            )
            reply = response.text.strip()
            batch = _parse_batch_response(reply, batch)
            print(f"  Gemini 배치 {b_idx+1}/{len(batches)} 완료 ({len(batch)}건)")
            time.sleep(4)
        except Exception:
            for item in batch:
                item.setdefault("filter_score", 5)
            time.sleep(4)
        results.extend(batch)
    return results

def _filter_with_gpt(items: List[Dict]) -> List[Dict]:
    """OpenAI GPT-4o mini를 사용한 필터링"""
    # 키워드 폴백으로 대체 (필요 시 OpenAI SDK 연동 추가)
    return _filter_with_keywords(items)

def _filter_with_keywords(items: List[Dict]) -> List[Dict]:
    """AI 키가 없을 때 키워드 기반 단순 필터링"""
    for item in items:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        score = 5
        for kw in BIOTECH_KEYWORDS:
            if kw.lower() in text:
                score = 8
                break
        item["filter_score"] = score
        item["summary_ko"] = item.get("title", "")
    return items

def _parse_batch_response(reply: str, items: List[Dict]) -> List[Dict]:
    """배치 응답에서 JSON 배열을 파싱합니다."""
    try:
        json_match = re.search(r'\[.*\]', reply, re.DOTALL)
        if json_match:
            analyses = json.loads(json_match.group())
            for i, analysis in enumerate(analyses):
                if i < len(items):
                    items[i]["filter_score"] = analysis.get("score", 5)
                    items[i]["summary_ko"] = analysis.get("summary_ko", "")
                    items[i]["emerging_sector"] = analysis.get("emerging_sector", "")
                    items[i]["leading_companies"] = analysis.get("leading_companies", [])
                    items[i]["category"] = analysis.get("category", "unknown")
                    items[i]["urgency"] = analysis.get("urgency", "medium")
        else:
            raise ValueError("No JSON array found in response")
    except Exception as e:
        print(f"  [Filter] 파싱 오류: {e}")
        for item in items:
            item.setdefault("filter_score", 5)
            item.setdefault("summary_ko", item.get("title", ""))
            item.setdefault("emerging_sector", "Unknown")
            item.setdefault("leading_companies", [])
    return items

def _build_batch_prompt(items: List[Dict]) -> str:
    """배치 프롬프트를 생성합니다."""
    lines = []
    for i, item in enumerate(items):
        lines.append(
            f"[{i+1}] 제목: {item['title']}\n"
            f"    출처: {item['source']}\n"
            f"    요약: {item.get('summary', '')[:200]}"
        )
    batch_text = "\n\n".join(lines)
    return (
        f"아래 {len(items)}개 뉴스를 분석하여 각각에 대한 JSON 객체를 배열에 담아 응답하세요.\n"
        f"형식: [{{\"score\":..., \"summary_ko\":\"...\", \"emerging_sector\":\"...\", "
        f"\"leading_companies\":[...], \"category\":\"...\", \"urgency\":\"...\"}}, ...]\n\n"
        f"{batch_text}"
    )
