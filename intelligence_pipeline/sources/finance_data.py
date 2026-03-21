"""
Yahoo Finance 데이터 수집기
============================
Tier 1 소스: yfinance를 통해 관심 종목의 가격/거래량 이상치를 감지합니다.
"""

import hashlib
from datetime import datetime, timezone
from typing import List, Dict

try:
    import yfinance as yf
except ImportError:
    yf = None


def collect_finance_data(tickers: List[str], volume_spike_threshold: float = 2.0) -> List[Dict]:
    """
    관심 종목의 최신 가격 및 거래량 이상치를 수집합니다.
    
    Args:
        tickers: 종목 코드 리스트
        volume_spike_threshold: 평균 거래량 대비 N배 이상이면 알림
    
    Returns:
        거래량 급등 종목 리스트
    """
    if yf is None:
        print("[Finance] yfinance 미설치 — pip install yfinance 실행 필요")
        return []
    
    results = []
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if hist.empty or len(hist) < 5:
                continue
            
            # 최근 거래 데이터
            latest = hist.iloc[-1]
            avg_volume = hist["Volume"].iloc[:-1].mean()
            latest_volume = latest["Volume"]
            
            # 거래량 급등 감지
            volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0
            is_spike = volume_ratio >= volume_spike_threshold
            
            # 일간 변동률
            prev_close = hist["Close"].iloc[-2] if len(hist) >= 2 else latest["Close"]
            daily_change = ((latest["Close"] - prev_close) / prev_close) * 100
            
            item_id = hashlib.md5(f"{ticker}_{datetime.now().date()}".encode()).hexdigest()
            
            # numpy 타입을 Python native로 변환
            price = float(latest["Close"])
            
            # [🔥 지표 보정 로직] 국채 수익률 지수(^TNX, ^IRX)는 10을 곱한 수치이므로 10으로 나누어 실물 금리로 변환
            # 예: 야후 파이낸스 ^TNX 43.50 -> 실제 미 10년물 국채 금리 4.35%
            if ticker in ["^TNX", "^IRX"] and price > 1.0:
                price = price / 10.0
            
            vol = int(latest_volume)
            avg_vol = int(avg_volume)
            vol_ratio = float(round(volume_ratio, 2))
            change = float(round(daily_change, 2))
            spike = bool(is_spike)
            
            # 지표 종류에 따른 제목 구성
            if ticker.startswith("^") or ticker == "DX-Y.NYB":
                title_text = f"🌐 {ticker}: {price:.2f}{'%' if ticker in ['^TNX', '^IRX'] else ''} ({change:+.2f}%)"
            else:
                title_text = f"{'🔥 ' if spike else ''}{ticker}: ${price:.2f} ({change:+.2f}%)"
            
            item = {
                "id": item_id,
                "source": f"Yahoo Finance ({ticker})",
                "source_type": "finance",
                "title": title_text,
                "summary": (
                    f"{ticker} 현재가 {price:.2f}{'%' if ticker in ['^TNX', '^IRX'] else ''}, "
                    f"일간 변동 {change:+.2f}%, "
                    f"거래량 {vol:,} "
                    f"(평균 대비 {vol_ratio:.1f}배"
                    f"{' — 자금 이동 포착!' if spike else ''})"
                ),
                "url": f"https://finance.yahoo.com/quote/{ticker}",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "ticker": ticker,
                    "price": round(price, 2),
                    "daily_change_pct": change,
                    "volume": vol,
                    "avg_volume": avg_vol,
                    "volume_ratio": vol_ratio,
                    "is_spike": spike,
                }
            }
            
            # 거래량 급등 종목만 수집 (전체 데이터는 대시보드에서 별도 표시)
            if is_spike or abs(daily_change) >= 3.0:
                results.append(item)
                
        except Exception as e:
            print(f"[Finance] {ticker} 수집 실패: {e}")
            continue
    
    print(f"[Finance] {len(tickers)}개 종목 스캔, {len(results)}건 이상치 감지")
    return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    from config import WATCHLIST_TICKERS, VOLUME_SPIKE_THRESHOLD
    
    items = collect_finance_data(WATCHLIST_TICKERS, VOLUME_SPIKE_THRESHOLD)
    for item in items:
        print(f"\n{item['title']}")
        print(f"  {item['summary']}")
