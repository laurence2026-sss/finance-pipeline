import requests
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_alert(item: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    score = item.get("filter_score", 0)
    title = item.get("title", "")
    summary = item.get("summary_ko") or item.get("summary", "")
    sector = item.get("emerging_sector", "N/A")
    companies = ", ".join(item.get("leading_companies", []))
    url = item.get("url", "")

    text = (
        f"🚨 *[독점 정보 포착]*\n"
        f"🔥 점수: {score}/10 | 섹터: #{sector}\n"
        f"🏢 기업: {companies}\n\n"
        f"📌 *{title}*\n\n"
        f"📝 {summary[:150]}...\n\n"
        f"🔗 [원문보기]({url})"
    )

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(api_url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        print(f"✅ 알림 송신 완료: {title[:20]}")
    except:
        print("❌ 알림 실패")

def run_notifier(items: list, threshold: int = 9):
    for item in items:
        if item.get("filter_score", 0) >= threshold:
            send_alert(item)
