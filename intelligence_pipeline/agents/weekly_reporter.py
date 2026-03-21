"""
Agent 6: Weekly Smart Money Reporter (주간 스마트 머니 리포트)
===============================================================
매주 월요일 07:00 KST 실행.
지난 7일간 누적 데이터(daily_YYYY-MM-DD.json)를 분석하여
'기관 자금 이동 추적' 중심의 주간 전략 브리핑을 텔레그램으로 발송.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import (
    DATA_DIR,
    TELEGRAM_REPORT_BOT_TOKEN,
    TELEGRAM_REPORT_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    GROQ_API_KEY,
)
import requests

KST = timezone(timedelta(hours=9))
GROQ_MODEL = "llama-3.3-70b-versatile"

# 8대 섹터 정의
SECTORS = {
    "AI/반도체":         ["ai", "semiconductor", "chip", "nvidia", "tsmc", "hbm", "nand", "dram",
                          "gpu", "npu", "inference", "llm", "foundry", "wafer", "broadcom", "arm",
                          "silicon", "memory", "data center", "datacenter", "cooling"],
    "포토닉스/광학":      ["photonics", "optical", "laser", "coherent", "lumentum", "fabrinet",
                          "silicon photonics", "lidar", "fiber", "transceiver"],
    "우주/위성":          ["space", "satellite", "rocket", "launch", "orbit", "nasa", "rocket lab",
                          "rklb", "planet labs", "redwire", "blacksky", "spacex", "ula", "ndaa"],
    "로보틱스":           ["robot", "humanoid", "optimus", "automation", "drone", "autonomous",
                          "teradyne", "tesla", "boston dynamics", "figure", "1x"],
    "바이오/제약":        ["bio", "pharma", "drug", "fda", "clinical", "trial", "cancer", "therapy",
                          "crispr", "glp", "longevity", "aging", "biotech", "antibody", "mrna",
                          "gene", "rare disease", "ipo biotech"],
    "자금 흐름":          ["macro", "fed", "rate", "inflation", "recession", "hedge", "whale",
                          "insider", "13f", "sec form", "buffett", "fund", "treasury", "yield",
                          "fomc", "gdp", "cpi", "tariff", "geopolit", "war", "sanction", "liquidity",
                          "dollar index", "vix", "rates", "interest rate", "m2", "central bank"],
    "에너지/자원":        ["energy", "nuclear", "uranium", "smr", "copper", "lithium", "battery",
                          "oil", "gas", "solar", "wind", "grid", "urnm", "copx", "lit"],
    "블록체인/크립토":    ["crypto", "bitcoin", "ethereum", "stablecoin", "tether", "usdc", "defi",
                          "blockchain", "coinbase", "mstr", "jpmorgan", "token", "digital asset"],
}


def load_weekly_items() -> List[dict]:
    """최근 7일간의 daily JSON 데이터를 합쳐서 반환합니다."""
    now = datetime.now(KST)
    all_items: List[dict] = []
    seen_ids: set = set()

    for days_ago in range(7):
        date_str = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        path = os.path.join(DATA_DIR, f"daily_{date_str}.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    item_id = item.get("id", "")
                    if item_id and item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_items.append(item)
        except Exception as e:
            print(f"[WeeklyReporter] {date_str} 로드 실패: {e}")

    print(f"[WeeklyReporter] 최근 7일 누적 데이터 로드: {len(all_items)}건")
    return all_items


def group_by_sector(items: List[dict]) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {s: [] for s in SECTORS}
    for item in items:
        text = " ".join([
            item.get("emerging_sector", ""),
            item.get("title", ""),
            item.get("summary_ko", ""),
            item.get("category", ""),
        ]).lower()

        matched: Optional[str] = None
        best_count: int = 0
        for sector, keywords in SECTORS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > best_count:
                best_count = count
                matched = sector

        if matched is not None and best_count > 0:
            groups[matched].append(item)

    for sector in groups:
        groups[sector].sort(key=lambda x: (
            1 if "독점" in x.get("korea_status", "") else 0,
            x.get("filter_score", 0)
        ), reverse=True)

    return groups


def compute_weekly_stats(items: List[dict], groups: Dict[str, List[dict]]) -> Dict[str, any]:
    sector_ranking = sorted(
        [(sector, len(items_list)) for sector, items_list in groups.items()],
        key=lambda x: x[1],
        reverse=True
    )
    sector_tags: Dict[str, int] = {}
    for item in items:
        tag = item.get("emerging_sector", "").strip()
        if tag:
            sector_tags[tag] = sector_tags.get(tag, 0) + 1
    top_tags = sorted(sector_tags.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total": len(items),
        "exclusive": sum(1 for i in items if "독점" in i.get("korea_status", "")),
        "early": sum(1 for i in items if "초기" in i.get("korea_status", "")),
        "sector_ranking": sector_ranking,
        "top_tags": top_tags,
    }


def build_sector_input(groups: Dict[str, List[dict]]) -> str:
    lines: List[str] = []
    for sector, items in groups.items():
        if not items:
            lines.append(f"\n[{sector}] (0건)\n  (해당 주간 데이터 없음)")
            continue
        lines.append(f"\n[{sector}] ({len(items)}건)")
        for item in items[:15]:
            status = "🔥독점" if "독점" in item.get("korea_status", "") else \
                     "⚡초기" if "초기" in item.get("korea_status", "") else "⚪반영"
            score = item.get("filter_score", 0)
            title = item.get("title", "")
            summary = item.get("summary_ko") or item.get("summary", "")
            lines.append(f"  ({score}점/{status}) {title}")
            if summary:
                lines.append(f"  → {summary[:150]}")
    return "\n".join(lines)


SYSTEM_PROMPT = """# ROLE
당신은 주간 글로벌 스마트 머니 전략 애널리스트입니다.
제공된 7일치 뉴스·데이터에만 근거하여 분석하며,
데이터에 없는 내용을 추론·생성하는 것을 엄격히 금합니다.

# 스마트 머니 정의 (이 범주만 분석 대상으로 인정)
- 기관 투자자: 연기금, 국부펀드, 보험사의 포트폴리오 변화
- 헤지펀드: 13F 공시, COT 리포트, 대형 포지션 변화
- 월가 거물: Berkshire, Bridgewater, Citadel 등 주요 운용사 행보
- 내부자: 임원급 내부자 매수/매도 공시

# 데이터 처리 원칙
- 7일치 데이터 중 주 후반(목~금) 데이터에 더 높은 가중치 부여
- 최소 2개 이상의 독립된 시그널이 겹쳐야 "확인된 흐름"으로 기술
- 시그널 1개뿐인 경우: "포착된 시그널"로 표기하고 확정 표현 사용 금지

---

# OUTPUT STRUCTURE

## 📈 Weekly Smart Money Report | {MM/DD ~ MM/DD}

---

### 🔹 Part 1: 이번 주 매크로 환경 — 유동성의 방향

**① 매크로 3중주 요약**
| 지표 | 주초 | 주말 | 변화 | 해석 |
|------|------|------|------|------|
| 10Y 국채 수익률 | X.XX% | X.XX% | ±X bp | |
| 달러인덱스(DXY) | XXX.X | XXX.X | ±X% | |
| VIX | XX.X | XX.X | ±X% | |

→ **종합 유동성 판단**: [위험선호(Risk-On) / 위험회피(Risk-Off) / 혼조]
→ **성장주 vs 가치주 로테이션**: [어느 방향으로 자금이 기울었는지, 근거 수치 포함 2문장]

**② 금주 스마트 머니 자금 이동 지도**

| 자금 주체 | 이동 섹터/자산 | 방향 | 핵심 근거 | 관련 티커 |
|-----------|---------------|------|-----------|-----------|
| [기관명/유형] | [섹터] | 매수/매도/중립 | [구체적 데이터] | $XXX |

---

### 🔹 Part 2: 다음 주 자금 이동 예상 경로
> ⚠️ 이 파트는 예측입니다. 이번 주 데이터에서 포착된 시그널에만 근거합니다.

**① [예측 제목]**
- 신뢰도: ★★★☆☆ (5점 만점)
- 근거: [구체적 수치 포함 데이터]
- 전제 조건: [필요 조건]
- 수혜 예상 섹터/종목: [$XXX]
- 무효화 시나리오: [뒤집을 변수]

---

### 🔹 Part 3: 이번 주 핵심 포인트 Top 3
**① [포인트 제목]**
[구조적 의미 서술, 3~4문장]
관련 티커: $XXX, $XXX

---

# RULES
- 모든 수치는 구체적으로 (예: "+1.8%", "+23bp")
- 데이터 공백 구간은 "해당 주간 데이터 없음"으로 처리
- 출력 언어: 한국어 (티커·고유명사·지표명 제외)
"""

USER_PROMPT_TEMPLATE = """아래는 [{start_date}] ~ [{end_date}] 수집된 섹터별 인텔리전스 데이터입니다.
이 데이터를 바탕으로 위 ROLE과 OUTPUT STRUCTURE에 맞춰 주간 전략 보고서를 작성하세요.

{sector_input}"""


def generate_weekly_report(groups: Dict[str, List[dict]], stats: Dict[str, any]) -> str:
    now = datetime.now(KST)
    end_date = now.strftime("%m/%d")
    start_date = (now - timedelta(days=6)).strftime("%m/%d")

    header = (
        f"📈 *Weekly Smart Money Report | {start_date} ~ {end_date}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 수집 {stats['total']}건  🔥 독점 {stats['exclusive']}건  ⚡ 초기 {stats['early']}건\n\n"
    )

    sector_input = build_sector_input(groups)

    if not GROQ_API_KEY:
        header + " (API KEY MISSING)"

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            start_date=start_date,
            end_date=end_date,
            sector_input=sector_input,
        )
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=GROQ_MODEL,
            temperature=0.2,
            max_tokens=3000,
        )
        return header + resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WeeklyReporter] 실패: {e}")
        return header + "주간 분석 생성 실패"


def send_telegram(text: str):
    bot_token = TELEGRAM_REPORT_BOT_TOKEN or TELEGRAM_BOT_TOKEN
    chat_id   = TELEGRAM_REPORT_CHAT_ID or TELEGRAM_CHAT_ID
    if not bot_token or not chat_id:
        return
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        requests.post(api_url, json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"}, timeout=15)


def run_weekly_reporter():
    items = load_weekly_items()
    if not items:
        return
    groups = group_by_sector(items)
    stats = compute_weekly_stats(items, groups)
    report = generate_weekly_report(groups, stats)
    send_telegram(report)


if __name__ == "__main__":
    run_weekly_reporter()
