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

# ============================================================
# 8대 섹터 정의 (reporter.py와 동일 — DRY 원칙상 import해도 되지만,
# 독립 실행 보장을 위해 여기에도 명시)
# ============================================================
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
    "기관들의 자금 이동": ["macro", "fed", "rate", "inflation", "recession", "hedge", "whale",
                          "insider", "13f", "sec form", "buffett", "fund", "treasury", "yield",
                          "fomc", "gdp", "cpi", "tariff", "geopolit", "war", "sanction"],
    "에너지/자원":        ["energy", "nuclear", "uranium", "smr", "copper", "lithium", "battery",
                          "oil", "gas", "solar", "wind", "grid", "urnm", "copx", "lit"],
    "블록체인/크립토":    ["crypto", "bitcoin", "ethereum", "stablecoin", "tether", "usdc", "defi",
                          "blockchain", "coinbase", "mstr", "jpmorgan", "token", "digital asset"],
}


# ============================================================
# 1. 데이터 로드: 최근 7일치 daily JSON 수합
# ============================================================
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


# ============================================================
# 2. 섹터별 분류 (빈 섹터도 유지)
# ============================================================
def group_by_sector(items: List[dict]) -> Dict[str, List[dict]]:
    """8개 섹터로 분류. 빈 섹터도 그대로 유지합니다."""
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

    # 각 섹터 내 점수 내림차순 정렬
    for sector in groups:
        groups[sector].sort(key=lambda x: (
            1 if "독점" in x.get("korea_status", "") else 0,
            x.get("filter_score", 0)
        ), reverse=True)

    return groups


# ============================================================
# 3. 주간 통계 산출
# ============================================================
def compute_weekly_stats(items: List[dict], groups: Dict[str, List[dict]]) -> Dict[str, any]:
    """주간 핵심 통계를 산출합니다."""
    exclusive = sum(1 for i in items if "독점" in i.get("korea_status", ""))
    early = sum(1 for i in items if "초기" in i.get("korea_status", ""))

    # 섹터별 건수 랭킹 (내림차순)
    sector_ranking = sorted(
        [(sector, len(items_list)) for sector, items_list in groups.items()],
        key=lambda x: x[1],
        reverse=True
    )

    # 가장 자주 등장한 키워드/섹터 태그
    sector_tags: Dict[str, int] = {}
    for item in items:
        tag = item.get("emerging_sector", "").strip()
        if tag:
            sector_tags[tag] = sector_tags.get(tag, 0) + 1
    top_tags = sorted(sector_tags.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total": len(items),
        "exclusive": exclusive,
        "early": early,
        "sector_ranking": sector_ranking,
        "top_tags": top_tags,
    }


# ============================================================
# 4. Groq용 섹터별 원본 데이터 텍스트 구성
# ============================================================
def build_sector_input(groups: Dict[str, List[dict]]) -> str:
    """Groq에 넘길 섹터별 원본 데이터 텍스트 구성."""
    lines: List[str] = []
    for sector, items in groups.items():
        if not items:
            lines.append(f"\n[{sector}] (0건)\n  (이번 주 수집된 유의미한 시그널 없음)")
            continue

        lines.append(f"\n[{sector}] ({len(items)}건)")
        for item in items[:15]:  # 주간이므로 섹터당 최대 15개 전달
            status = "🔥독점" if "독점" in item.get("korea_status", "") else \
                     "⚡초기" if "초기" in item.get("korea_status", "") else "⚪반영"
            score = item.get("filter_score", 0)
            title = item.get("title", "")
            summary = item.get("summary_ko") or item.get("summary", "")
            sector_tag = item.get("emerging_sector", "")
            lines.append(f"  ({score}점/{status}) [{sector_tag}] {title}")
            if summary:
                lines.append(f"  → {summary[:150]}")
    return "\n".join(lines)


# ============================================================
# 5. 주간 전용 프롬프트 (스마트 머니 추적 특화)
# ============================================================
WEEKLY_SYSTEM_PROMPT = """당신은 한국 개인투자자 전용 '주간 글로벌 스마트 머니 전략 애널리스트'입니다.

## 핵심 임무
지난 7일간 수집된 글로벌 뉴스·데이터를 종합 분석하여,
"돈이 어디서 빠지고, 어디로 몰리고 있는가"를 추적하는 전략 보고서를 작성합니다.

## 절대 하지 않을 것
- 개별 뉴스의 단순 나열 (일일 브리핑이 아닙니다)
- 이미 시장에 반영된 뻔한 정보의 재탕
- 근거 없는 낙관적/비관적 전망

## 반드시 할 것
- 7일간의 파편화된 뉴스들을 종합하여 '패턴'과 '자금 이동 방향'을 추론
- 기관 매수/매도, 내부자 거래, ETF 자금 유입·유출을 최우선으로 분석
- 한국 시장에 아직 미반영된 정보를 특별히 강조

## 출력 형식 (반드시 준수)

📈 Weekly Smart Money Report | {날짜 범위}

━━━━━━━━━━━━━━━━━━━━━━

🔹 Part 1: 이번 주 스마트 머니는 어디로 향했나?
  • (섹터명) 무슨 자금이, 왜 이동했는가 → 핵심 근거 (관련 티커)
  • ...
  [3~5개 항목]

🔹 Part 2: 다음 주 유력 자금 이동 예상 경로
  ① [예측 제목]
  → 근거: [이번 주 데이터에서 포착된 구체적 시그널]
  → 수혜 예상: [섹터/종목]
  ② ...
  [2~3개 항목]

🔹 Part 3: 주간 최우선 감시 대상 (Top 3 Conviction Ideas)
  🥇 [1순위 아이디어] — 왜 지금인가?
  🥈 [2순위 아이디어] — 왜 지금인가?
  🥉 [3순위 아이디어] — 왜 지금인가?

━━━━━━━━━━━━━━━━━━━━━━
⚠️ 본 리포트는 AI가 공개 데이터를 분석한 참고 자료이며, 투자 조언이 아닙니다."""


WEEKLY_USER_PROMPT_TEMPLATE = """아래는 [{start_date}] ~ [{end_date}] 7일간 수집된 섹터별 인텔리전스 데이터입니다.

## 주간 통계 요약
- 총 수집: {total}건
- 🔥 한국 미반영(독점): {exclusive}건
- ⚡ 초기 반영: {early}건
- 섹터 건수 랭킹: {sector_ranking}
- 주간 핫 키워드 TOP 10: {top_tags}

## 처리 지침
1. 개별 뉴스를 나열하지 마세요. 7일간의 뉴스들을 종합하여 '큰 그림(Big Picture)'을 그리세요.
2. 특히 "기관들의 자금 이동" 섹터의 데이터를 가장 깊이 분석하세요. 내부자 매수, 헤지펀드 포트폴리오 변경, ETF 볼륨 급증 등.
3. 섹터 간 교차 분석을 하세요. 예: "AI 반도체 쇼티지 → 에너지(전력) 수요 폭증 → 우라늄/SMR 수혜"
4. Part 2에서는 이번 주 데이터로부터 연역적으로 추론 가능한 '다음 주 전망'을 대담하게 제시하세요.

## 섹터별 원본 데이터

{sector_input}"""


# ============================================================
# 6. Groq 호출 및 리포트 생성
# ============================================================
def generate_weekly_report(
    groups: Dict[str, List[dict]],
    stats: Dict[str, any],
) -> str:
    """Groq를 호출하여 주간 리포트를 생성합니다. 실패 시 Fallback."""
    now = datetime.now(KST)
    end_date = now.strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=6)).strftime("%Y-%m-%d")

    header = (
        f"📈 *Weekly Smart Money Report*\n"
        f"📅 {start_date} ~ {end_date}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 총 {stats['total']}건  🔥 독점 {stats['exclusive']}건  "
        f"⚡ 초기 {stats['early']}건\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    sector_input = build_sector_input(groups)

    if not GROQ_API_KEY:
        print("[WeeklyReporter] GROQ_API_KEY 없음 — Fallback 모드")
        return header + _fallback_body(groups, stats)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        # 섹터 랭킹/태그를 문자열로 변환
        ranking_str = ", ".join(
            f"{s}({c}건)" for s, c in stats["sector_ranking"]
        )
        tags_str = ", ".join(
            f"{tag}({cnt}회)" for tag, cnt in stats["top_tags"]
        )

        user_prompt = WEEKLY_USER_PROMPT_TEMPLATE.format(
            start_date=start_date,
            end_date=end_date,
            total=stats["total"],
            exclusive=stats["exclusive"],
            early=stats["early"],
            sector_ranking=ranking_str,
            top_tags=tags_str,
            sector_input=sector_input,
        )

        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": WEEKLY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=GROQ_MODEL,
            temperature=0.4,
            max_tokens=3500,
        )
        body = resp.choices[0].message.content.strip()
        return header + body

    except Exception as e:
        print(f"[WeeklyReporter] Groq 실패: {e}")
        return header + _fallback_body(groups, stats)


# ============================================================
# 7. Fallback (Groq 실패 시 비상용 리포트)
# ============================================================
def _fallback_body(groups: Dict[str, List[dict]], stats: Dict[str, any]) -> str:
    """Groq 없을 때 단순 포맷으로 주간 요약."""
    lines: List[str] = []

    # 섹터별 건수 요약
    lines.append("📊 섹터별 주간 건수:")
    for sector, count in stats["sector_ranking"]:
        bar = "█" * min(count, 20)
        lines.append(f"  {sector}: {bar} ({count}건)")

    # 핫 키워드
    if stats["top_tags"]:
        lines.append("\n🔑 주간 핫 키워드:")
        lines.append("  " + ", ".join(f"{tag}({cnt})" for tag, cnt in stats["top_tags"]))

    # 섹터별 TOP 3 뉴스
    for sector, items in groups.items():
        lines.append(f"\n【{sector}】")
        if not items:
            lines.append("• 이번 주 유의미한 시그널 없음")
            continue

        for item in items[:3]:
            status = "🔥" if "독점" in item.get("korea_status", "") else \
                     "⚡" if "초기" in item.get("korea_status", "") else "⚪"
            summary = item.get("summary_ko") or item.get("title", "")
            lines.append(f"• {summary[:100]} ({item.get('filter_score', 0)}점 {status})")

    return "\n".join(lines)


# ============================================================
# 8. 텔레그램 발송
# ============================================================
def send_telegram(text: str) -> None:
    """텔레그램으로 리포트를 발송합니다. 4096자 제한 분할 처리."""
    bot_token = TELEGRAM_REPORT_BOT_TOKEN or TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_REPORT_CHAT_ID or TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        print("[WeeklyReporter] 텔레그램 키 없음 — 콘솔 출력")
        print(text)
        return

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = [text[i:i + 4096] for i in range(0, len(text), 4096)]

    for chunk in chunks:
        try:
            resp = requests.post(api_url, json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
            }, timeout=15)
            if resp.status_code == 200:
                print("[WeeklyReporter] 텔레그램 발송 완료")
            else:
                print(f"[WeeklyReporter] 텔레그램 오류: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[WeeklyReporter] 텔레그램 실패: {e}")


# ============================================================
# 9. 메인 실행
# ============================================================
def run_weekly_reporter() -> None:
    """주간 리포트의 메인 진입점."""
    print("=" * 60)
    print(f"📈 Agent 6 (Weekly Reporter) 시작 — "
          f"{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')} KST")
    print("=" * 60)

    items = load_weekly_items()
    if not items:
        print("[WeeklyReporter] 7일간 데이터 없음 — 빈 리포트 발송")
        now = datetime.now(KST)
        empty_msg = (
            f"📈 *Weekly Smart Money Report*\n"
            f"📅 {(now - timedelta(days=6)).strftime('%Y-%m-%d')} ~ "
            f"{now.strftime('%Y-%m-%d')}\n\n"
            f"이번 주 AI 필터(7점 이상)를 통과한 핵심 뉴스가 없습니다. "
            f"시장을 지속적으로 모니터링 중입니다. 🔭"
        )
        send_telegram(empty_msg)
        return

    groups = group_by_sector(items)
    stats = compute_weekly_stats(items, groups)

    print(f"  섹터 분류: {', '.join(f'{s}({len(v)}건)' for s, v in groups.items())}")
    print(f"  독점 {stats['exclusive']}건 / 초기 {stats['early']}건")

    report = generate_weekly_report(groups, stats)
    send_telegram(report)

    print(f"\n✅ Weekly Reporter 완료: {stats['total']}건 → 주간 브리핑 발송")


if __name__ == "__main__":
    run_weekly_reporter()
