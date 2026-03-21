"""
Agent 5: Daily Reporter (일일 브리핑 에이전트)
==============================================
매일 07:00 KST 실행.
지난 24시간 누적 데이터(daily_YYYY-MM-DD.json)를 읽어
섹터별 3~5개 선별 + 1줄 요약을 텔레그램으로 발송.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from config import DATA_DIR, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_REPORT_BOT_TOKEN, TELEGRAM_REPORT_CHAT_ID, GROQ_API_KEY
import requests

KST = timezone(timedelta(hours=9))
GROQ_MODEL = "llama-3.3-70b-versatile"

# 7개 섹터 정의 및 키워드 매핑
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
}


def load_daily_items() -> list:
    """오늘과 어제의 daily JSON 데이터를 합쳐서 반환합니다."""
    today = datetime.now(KST).strftime("%Y-%m-%d")
    yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")

    all_items = []
    seen_ids = set()

    for date in [today, yesterday]:
        path = os.path.join(DATA_DIR, f"daily_{date}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for item in items:
                        if item["id"] not in seen_ids:
                            seen_ids.add(item["id"])
                            all_items.append(item)
            except Exception:
                pass

    print(f"[Reporter] 최근 2일치 누적 데이터 로드: {len(all_items)}건")
    return all_items


def group_by_sector(items: list) -> dict:
    groups = {s: [] for s in SECTORS}

    for item in items:
        text = " ".join([
            item.get("emerging_sector", ""),
            item.get("title", ""),
            item.get("summary_ko", ""),
            item.get("category", ""),
        ]).lower()

        matched = None
        best_count = 0
        for sector, keywords in SECTORS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > best_count:
                best_count = count
                matched = sector

        target = matched if best_count > 0 else None
        if target:
            groups[target].append(item)

    # 각 섹터 내 점수 내림차순 정렬
    for sector in groups:
        groups[sector].sort(key=lambda x: (
            1 if "독점" in x.get("korea_status", "") else 0,
            x.get("filter_score", 0)
        ), reverse=True)

    # 항목이 없는 섹터도 그대로 반환하여 리포트에 명시되도록 함
    return groups


def build_sector_input(groups: dict) -> str:
    """Groq에 넘길 섹터별 원본 데이터 텍스트 구성."""
    lines = []
    for sector, items in groups.items():
        if not items:
            lines.append(f"\n[{sector}] (0건)\n  (오늘 수집된 유의미한 시그널 없음)")
            continue
            
        lines.append(f"\n[{sector}] ({len(items)}건)")
        for item in items[:10]:  # 섹터당 최대 10개 전달
            status = "🔥독점" if "독점" in item.get("korea_status", "") else \
                     "⚡초기" if "초기" in item.get("korea_status", "") else "⚪반영"
            score = item.get("filter_score", 0)
            title = item.get("title", "")
            summary = item.get("summary_ko") or item.get("summary", "")
            sector_tag = item.get("emerging_sector", "")
            lines.append(f"  ({score}점/{status}) [{sector_tag}] {title}")
            if summary:
                lines.append(f"  → {summary[:120]}")
    return "\n".join(lines)


SYSTEM_PROMPT = """당신은 한국 개인투자자를 위한 글로벌 금융·기술 인텔리전스 애널리스트입니다.

## 역할 정의
매일 밤 수집된 미국 경제·기술 뉴스를 분석하여,
돈의 이동과 수요 구조 변화 중심의 날카로운 한국어 브리핑을 작성합니다.

## 절대 포함하지 않을 것 (잡음 기준)
- 단순 실적 발표, 배당 변경, 경영진 교체 등 단발성 이벤트
- 이미 시장에 가격이 반영된 정보 (컨센서스 내 결과)

## 반드시 포함할 것 (신호 기준)
- 자본 흐름 변화: 기관 매수·매도, VC/PE 대규모 투자, 정부 보조금
- 수요 구조 급변: 신기술 채택으로 인한 특정 자원·부품·인프라 수요 폭증
  (예: AI 모델 고도화 → 데이터센터·전력 수요 급증)
- 공급망 병목: 독점적 공급자 등장 또는 쇼티지 심화
- 한국 시장 미반영 정보: 국내 언론 미보도 해외 독점 동향

## 섹터 분류
【AI/반도체】 【포토닉스/광학】 【우주/위성】 【로보틱스】 【바이오/제약】 【기관들의 자금 이동】 【에너지/자원】

## 출력 형식 (반드시 준수)

【섹터명】
핵심 이슈: [이 섹터에서 오늘 가장 중요한 흐름 1문장]

• (등급) 무슨 일 → 왜 중요한가 (관련 티커)
• (등급) 무슨 일 → 왜 중요한가 (관련 티커)
• ...

📌 주목 포인트
① [포인트 제목]
→ 근거: [구체적 수치·발언·데이터]
→ 투자 시사점: [어떤 섹터/종목에 어떻게 영향을 미치는가]

② [포인트 제목]
→ 근거:
→ 투자 시사점:

(3~5개, 동일 형식 반복)

---"""

USER_PROMPT_TEMPLATE = """아래는 오늘 [{date}] 수집된 섹터별 원본 인텔리전스 데이터입니다.

## 처리 지침
1. 각 섹터에서 투자 임팩트가 높은 항목을 3~5개 선별하세요.
2. 동일 이슈가 중복될 경우, 가장 상위 점수 항목 1개만 사용하세요.
3. 데이터가 없는 섹터는 "오늘 유의미한 시그널 없음"으로 명시하세요.

## 1줄 요약 작성 원칙
- 구조: "무슨 일" + "→" + "왜 중요한가 (투자 임팩트)" + "(관련 티커)"
- 예시: "TSMC N3 공급 쇼티지 심화 → 대체 파운드리 수요 전환 가능성 (AVGO, COHR 주목)"
- 가격 등락·단순 수치 나열 금지. 반드시 인과관계로 연결할 것.

## 원본 데이터

{sector_input}"""


def generate_report(groups: dict, total: int, exclusive: int, early: int) -> str:
    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    header = (
        f"📊 *Daily Intel Brief | {today_str}*\n"
        f"────────────────────\n"
        f"📡 수집 {total}건  🔥 독점 {exclusive}건  ⚡ 초기 {early}건\n"
        f"────────────────────\n\n"
    )

    sector_input = build_sector_input(groups)

    if not GROQ_API_KEY:
        return header + _fallback_body(groups)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            date=today_str,
            sector_input=sector_input,
        )
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model=GROQ_MODEL,
            temperature=0.3,
            max_tokens=2500,
        )
        body = resp.choices[0].message.content.strip()
        return header + body
    except Exception as e:
        print(f"[Reporter] Groq 실패: {e}")
        return header + _fallback_body(groups)


def _fallback_body(groups: dict) -> str:
    """Groq 없을 때 단순 포맷."""
    lines = []
    for sector, items in groups.items():
        lines.append(f"\n【{sector}】")
        if not items:
            lines.append("• 오늘 유의미한 시그널 없음")
            continue
            
        for item in items[:4]:
            status = "🔥" if "독점" in item.get("korea_status", "") else \
                     "⚡" if "초기" in item.get("korea_status", "") else "⚪"
            summary = item.get("summary_ko") or item.get("title", "")
            lines.append(f"• {summary[:80]} ({item.get('filter_score', 0)}점 {status})")
    return "\n".join(lines)


def send_telegram(text: str):
    # 보고서 전용 봇/채팅방 우선, 없으면 기존 봇으로 폴백
    bot_token = TELEGRAM_REPORT_BOT_TOKEN or TELEGRAM_BOT_TOKEN
    chat_id   = TELEGRAM_REPORT_CHAT_ID or TELEGRAM_CHAT_ID
    if not bot_token or not chat_id:
        print("[Reporter] 텔레그램 키 없음 — 콘솔 출력")
        print(text)
        return

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
    for chunk in chunks:
        try:
            resp = requests.post(api_url, json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
            }, timeout=10)
            if resp.status_code == 200:
                print("[Reporter] 텔레그램 발송 완료")
            else:
                print(f"[Reporter] 텔레그램 오류: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[Reporter] 텔레그램 실패: {e}")


def run_reporter():
    print("=" * 60)
    print(f"📊 Agent 5 (Reporter) 시작 — {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')} KST")
    print("=" * 60)

    items = load_daily_items()
    if not items:
        print("[Reporter] 데이터 없음 — 빈 리포트 발송")
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        empty_msg = f"📊 *Daily Intel Brief | {today_str}*\n\n안녕하세요! 지난 24시간 동안 AI 필터(7점 이상)를 통과한 새로운 핵심 뉴스가 없습니다. 시장을 지속적으로 모니터링 중입니다. 🔭"
        send_telegram(empty_msg)
        return

    exclusive = sum(1 for i in items if "독점" in i.get("korea_status", ""))
    early     = sum(1 for i in items if "초기" in i.get("korea_status", ""))
    groups    = group_by_sector(items)

    print(f"  섹터 분류: {', '.join(f'{s}({len(v)}건)' for s, v in groups.items())}")

    report = generate_report(groups, len(items), exclusive, early)
    send_telegram(report)

    print(f"\n✅ Reporter 완료: {len(items)}건 → 브리핑 발송")


if __name__ == "__main__":
    run_reporter()
