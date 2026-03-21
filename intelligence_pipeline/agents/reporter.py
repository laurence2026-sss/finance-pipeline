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

from config import DATA_DIR, TELEGRAM_REPORT_BOT_TOKEN, TELEGRAM_REPORT_CHAT_ID, GROQ_API_KEY
import requests

KST = timezone(timedelta(hours=9))
GROQ_MODEL = "llama-3.3-70b-versatile"

# 8대 섹터 정의 및 키워드 매핑
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

    return groups


def build_sector_input(groups: dict) -> str:
    """Groq에 넘길 섹터별 원본 데이터 텍스트 구성."""
    lines = []
    for sector, items in groups.items():
        if not items:
            lines.append(f"\n[{sector}] (0건)\n  (오늘 수집된 유의미한 시그널 없음)")
            continue
            
        lines.append(f"\n[{sector}] ({len(items)}건)")
        for item in items[:10]:
            status = "🔥독점" if "독점" in item.get("korea_status", "") else \
                     "⚡초기" if "초기" in item.get("korea_status", "") else "⚪반영"
            score = item.get("filter_score", 0)
            title = item.get("title", "")
            summary = item.get("summary_ko") or item.get("summary", "")
            lines.append(f"  ({score}점/{status}) {title}")
            if summary:
                lines.append(f"  → {summary[:120]}")
    return "\n".join(lines)


SYSTEM_PROMPT = """# ROLE
당신은 한국 개인투자자를 위한 글로벌 금융·기술 인텔리전스 애널리스트입니다.
제공된 뉴스 원문을 바탕으로, 매일 아침 섹터별 브리핑을 작성합니다.
추측이나 배경지식 기반의 내용을 생성하지 말고, 반드시 제공된 뉴스에 근거해서만 작성하세요.
해당 섹터의 뉴스가 없으면 "오늘 주요 뉴스 없음"으로 처리하고 내용을 생성하지 마세요.

---

# OUTPUT STRUCTURE

## 🌐 오늘의 시장 맥락 (브리핑 최상단 고정)
- 금리(10Y 국채 수익률), 달러인덱스(DXY), VIX의 전일 대비 변화를 수치로 명시
- 위 세 지표의 동시 변화가 오늘 전체 섹터에 미치는 자금 유입/유출 방향을 2~3줄로 요약
- 예: "DXY 급등 + VIX 상승 → 위험자산 회피, 신흥국 자금 이탈 압력"

---

## 섹터별 브리핑

각 섹터는 아래 형식을 반드시 따릅니다.

【섹터명】
📋 핵심 흐름: [이 섹터 오늘의 핵심 방향성 또는 이슈 1문장]

- [뉴스 제목 또는 한 줄 요약] (관련 티커: $XXX)
  → 왜 중요한가: [시장/투자자 관점에서의 영향력, 1~2문장]

- [뉴스 제목 또는 한 줄 요약] (관련 티커: $XXX)
  → 왜 중요한가: [시장/투자자 관점에서의 영향력, 1~2문장]

📌 오늘의 주목 포인트 (해당 섹터에서 가장 중요한 3~5가지만 선별)
  1. [포인트 제목]: [구체적 수치·배경·영향 포함, 2~3문장]
  2. ...

---

# 섹터 목록 (아래 순서대로 출력)
1. 【AI/반도체】엔비디아, TSMC, HBM, 데이터센터, 쿨링 시스템 등
2. 【포토닉스/광학】실리콘 포토닉스, 광통신, 레이저 등
3. 【우주/위성】스페이스X, 로켓랩, 위성통신, NASA 등
4. 【로보틱스】휴머노이드, 테슬라 옵티머스, 보스턴 다이나믹스, 공장 자동화 등
5. 【바이오/제약】임상 결과, FDA 승인, 암 치료제, 역노화 기술 등
6. 【자금 흐름】헤지펀드 포지션 변화, 내부자 매수/매도, 기관 수급 등
7. 【에너지/자원】우라늄·SMR, 배터리, 구리·리튬 등 핵심 광물
8. 【블록체인/크립토】비트코인, 이더리움, 스테이블코인, 대형 기관 디지털 자산 동향

---

# RULES
- 모든 수치는 구체적으로 명시 (예: "급등"이 아니라 "+3.2%")
- 한국 개인투자자 관점에서 실질적으로 행동 가능한 인사이트 중심으로 서술
- 뉴스 없는 섹터: "오늘 주요 뉴스 없음" 한 줄로 마감, 내용 생성 금지
- 출력 언어: 한국어 (티커·고유명사 제외)
"""

USER_PROMPT_TEMPLATE = """아래는 오늘 [{date}] 수집된 섹터별 원본 인텔리전스 데이터입니다.
이 데이터를 바탕으로 위 ROLE과 OUTPUT STRUCTURE에 맞춰 브리핑을 작성하세요.

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
            lines.append("• 오늘 주요 뉴스 없음")
            continue
            
        for item in items[:4]:
            status = "🔥" if "독점" in item.get("korea_status", "") else \
                     "⚡" if "초기" in item.get("korea_status", "") else "⚪"
            summary = item.get("summary_ko") or item.get("title", "")
            lines.append(f"• {summary[:80]} ({item.get('filter_score', 0)}점 {status})")
    return "\n".join(lines)


def send_telegram(text: str):
    # 유저 지정: 매일 아침 브리핑은 TELEGRAM_REPORT_... 사용
    bot_token = TELEGRAM_REPORT_BOT_TOKEN
    chat_id   = TELEGRAM_REPORT_CHAT_ID
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
