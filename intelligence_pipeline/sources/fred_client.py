"""
FRED API Client
================
미 연준 경제 데이터베이스(FRED)에서 기준 금리, VIX 등의
매크로 데이터를 주간 단위(최솟값, 최댓값, 현재값)로 정확하게 수집합니다.
"""

import requests
from datetime import datetime, timedelta

# FRED 시리즈 코드 정의
# DGS10: 10-Year Treasury Constant Maturity Rate
# VIXCLS: CBOE Volatility Index
# DTWEXBGS: Trade Weighted U.S. Dollar Index: Broad (가장 널리 쓰이는 FRED 달러 인덱스)
FRED_SERIES_MAP = {
    "US10Y": "DGS10",
    "VIX": "VIXCLS",
    "DXY": "DTWEXBGS"
}

def get_fred_weekly_stats(api_key: str, series_id: str) -> dict:
    """최근 7일간의 최솟값, 최댓값, 현재값을 반환합니다."""
    if not api_key:
        return {"min": "N/A", "max": "N/A", "current": "N/A"}
        
    url = "https://api.stlouisfed.org/fred/series/observations"
    # 휴일 등을 감안해 14일 전부터 가져온 뒤 최신 데이터만 필터링
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
        "sort_order": "asc"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "error_message" in data:
            print(f"[FRED Client] API 오류 ({series_id}): {data['error_message']}")
            return {"min": "N/A", "max": "N/A", "current": "N/A"}
            
        observations = [obs for obs in data.get("observations", []) if obs["value"] != "."]
        
        if not observations:
             return {"min": "N/A", "max": "N/A", "current": "N/A"}
        
        # 최근 7개의 거래일 데이터만 사용
        recent_obs = observations[-7:]
        values = [float(obs["value"]) for obs in recent_obs]
        
        return {
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "current": round(values[-1], 2)
        }
    except Exception as e:
        print(f"[FRED Client] {series_id} 네트워크 통신 오류: {e}")
        return {"min": "N/A", "max": "N/A", "current": "N/A"}

def get_all_macro_stats(api_key: str) -> dict:
    """US10Y, VIX, DXY의 전체 통계를 딕셔너리로 반환합니다."""
    return {
        "US10Y": get_fred_weekly_stats(api_key, FRED_SERIES_MAP["US10Y"]),
        "VIX": get_fred_weekly_stats(api_key, FRED_SERIES_MAP["VIX"]),
        "DXY": get_fred_weekly_stats(api_key, FRED_SERIES_MAP["DXY"])
    }
