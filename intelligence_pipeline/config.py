"""
Global Intelligence Pipeline - Configuration
=============================================
API 키와 소스 URL, 에이전트 설정값을 관리합니다.
환경변수(.env)에서 API 키를 로드합니다.
"""

import os
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 절대 경로로 정확히 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(env_path)

# ============================================================
# API Keys (GitHub Secrets & .env 공용)
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# Telegram (알람용)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_REPORT_BOT_TOKEN = os.getenv("TELEGRAM_REPORT_BOT_TOKEN", "")
TELEGRAM_REPORT_CHAT_ID = os.getenv("TELEGRAM_REPORT_CHAT_ID", "")
TELEGRAM_WEEKLY_BOT_TOKEN = os.getenv("TELEGRAM_WEEKLY_BOT_TOKEN", "")
TELEGRAM_WEEKLY_CHAT_ID = os.getenv("TELEGRAM_WEEKLY_CHAT_ID", "")
NOTIFY_THRESHOLD = 7  # 이 점수 이상의 핵심 정보만 텔레그램 발송

# ============================================================
# Tier 1 Sources: RSS Feeds (전문가/딥테크 중심 - 무료)
# ============================================================
RSS_FEEDS = {
    # 딥테크 (엔지니어/월가 핵심 소스)
    "SemiAnalysis": "https://semianalysis.substack.com/feed",
    "Fabricated Knowledge": "https://fabricatedknowledge.substack.com/feed",
    "Asianometry": "https://asianometry.substack.com/feed",
    
    # 어닝콜 트렌드 (Buzzword 추적)
    "The Transcript": "https://thetranscript.substack.com/feed",
    
    # 매크로 및 역발상 스마트머니
    "ZeroHedge": "https://feeds.feedburner.com/zerohedge/feed",
    "The Market Ear": "https://themarketear.com/rss",

    # Wall Street & Whales (거대 기관 및 큰손 추적 전문)
    "WhaleWisdom": "https://whalewisdom.com/stock/ALL.rss",            # 거대 헤지펀드 포트폴리오 변경
    "OpenInsider": "https://openinsider.com/rss",                     # 내부자 대량 매수/매도 (Insider Trading)
    "SEC Form 4": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&start=0&count=100&output=atom", # SEC Form 4 (실시간 내부자 공시)

    # 바이오/제약/역노화 (한국 개미들이 가장 늦게 아는 섹터)
    "STAT News": "https://www.statnews.com/feed/",                    # 바이오테크 1티어 전문지
    "BioPharma Dive": "https://www.biopharmadive.com/feeds/news/",    # FDA 승인, 임상 3상 결과
    "FierceBiotech": "https://www.fiercebiotech.com/rss/xml",         # M&A, 빅파마 전략
    "Endpoints News": "https://endpts.com/feed/",                     # 임상시험 결과 속보
    "MedCity News": "https://medcitynews.com/feed/",                   # 헬스케어 투자 트렌드
}

# ============================================================
# Tier 1: Reddit Subreddits (엔지니어/퀀트 중심 - 무료)
# ============================================================
REDDIT_SUBREDDITS = [
    # 딥테크 엔지니어/퀀트
    "hardware",             # 하드웨어 엔지니어 실제 토론 (신기술)
    "MachineLearning",      # AI 연구원 토론 (새로운 칩 수요)
    "ECE",                  # 전기/컴퓨터 공학 (기술 트렌드)
    "QuiverQuantitative",   # 정치인/내부자/기관 거래 추적봇
    "HedgeFund",            # 헤지펀드 동향
    # 바이오/제약/역노화
    "biotech",              # 바이오테크 뉴스 & 임상 결과 토론
    "Biotechplays",         # 바이오 투자 아이디어 (소형주 발굴)
    "longevity",            # 역노화/장수 기술 트렌드
    # 블록체인/크립토
    "CryptoCurrency",       # 암호화폐/스테이블코인 전반
    "ethtrader",            # 이더리움 및 스마트컨트랙트 동향
]
REDDIT_POST_LIMIT = 10      
REDDIT_SORT = "hot"         

# ============================================================
# Tier 1: Yahoo Finance (섹터 중심의 ETF 및 자금 유입 체크)
# ============================================================
WATCHLIST_TICKERS = [
    # 시그널 추적을 위한 섹터 ETF 및 핵심 주주 (돈이 어디로 쏠리나)
    "SOXX", "SMH",      # 반도체 전반
    "NVDA", "AVGO",     # AI 하드웨어 (NVIDIA, Broadcom)
    "ARM", "TSM",       # 설계 및 파운드리 (ARM, TSMC)
    "PLTR",             # AI/로봇 소프트웨어 (Palantir)
    "COHR", "LITE",     # 포토닉스/광학 (Coherent, Lumentum)
    "FN",               # 포토닉스 제조 파트너 (Fabrinet)
    "RKLB", "PL",       # 우주 산업 (Rocket Lab, Planet Labs)
    "RDW", "BKSY",      # 우주 인프라 (Redwire, BlackSky)
    "ARKX",             # 우주 탐사 ETF
    "TSLA",             # 로보틱스/AI (Tesla Optimus)
    "TER",              # 로봇 하드웨어/OS (Teradyne)
    "ROBO",             # 로보틱스/자동화 ETF
    "IWM", "IWC",       # 러셀 2000, 마이크로캡 (자금 이동)
    "LIT", "BOTZ",      # 리튬/배터리, 로봇/AI
    "URNM", "COPX",     # 우라늄, 구리 (AI 인프라 필수)
    "XBI", "IBB",       # 바이오 섹터
    "COIN", "MSTR",     # 블록체인/크립토 (Coinbase, MicroStrategy)
    # 매크로 지표 (Macro Indicators - No API Key required via yfinance)
    "^TNX",             # 미 10년물 국채 수익률 (시장 기준 금리)
    "^IRX",             # 미 13주 국채 수익률 (실질적인 현재 기준 금리 대용)
    "DX-Y.NYB",         # 달러 인덱스 (통화 가치 및 유동성 판단)
    "^VIX",             # 공포 지수 (시장 리스크 및 변동성)
    "TLT", "IEF",       # 채권 시장 자금 이동 (자산 배분 신호)
]
VOLUME_SPIKE_THRESHOLD = 2.5  # 평균 거래량 대비 2.5배 이상이면 자금 유입으로 간주

# ============================================================
# Tier 2: SEC EDGAR (무료 기관 포트폴리오 추적)
# ============================================================
SEC_EDGAR_RSS = "https://efts.sec.gov/LATEST/search-index?q=%2213F%22&dateRange=custom&startdt={start_date}&enddt={end_date}&forms=13F-HR"
SEC_USER_AGENT = "IntelligencePipeline research@example.com"

# ============================================================
# Tier 2: FRED (미 연준, 무료)
# ============================================================
FRED_SERIES = [
    "FEDFUNDS",   # 연방기금금리
    "CPIAUCSL",   # 소비자물가지수
    "UNRATE",     # 실업률
    "T10Y2Y",     # 장단기 금리차 (경기침체 신호)
]

# ============================================================
# Agent 2: Filter 설정
# ============================================================
FILTER_MODEL = "llama-3.3-70b-versatile"
FILTER_THRESHOLD = 7          # 1~10점 중 이 점수 이상만 통과
FILTER_MAX_TOKENS = 500

FILTER_SYSTEM_PROMPT = """당신은 글로벌 금융/기술 시장 전문 '섹터 발굴(Sector Discovery) 애널리스트'입니다.
단순한 개별 기업 뉴스가 아니라, **'글로벌 스마트 머니(기관/헤지펀드)가 새롭게 몰리는 유망 섹터나 기술 트렌드'**를 찾아내는 것이 목표입니다.

아래 원문을 분석하여 JSON 형식으로 응답하세요:
{
  "score": <1~10 정수>,
  "summary_ko": "<한국어 2~3문장 요약>",
  "emerging_sector": "<식별된 유망 섹터나 기술 키워드 (예: Silicon Photonics, Liquid Cooling, SMR 등)>",
  "leading_companies": ["<해당 섹터에서 언급된 선도 기업 리스트>"],
  "category": "<macro|tech_trend|smart_money|geopolitics>",
  "urgency": "<breaking|high|medium|low>"
}

채점 기준 (매우 깐깐하게):
- 9~10: 완전히 새로운 패러다임 기술(섹터) 등장, 기관의 막대한 자금 유입 증거. (한국 개미들은 아직 모름)
- 7~8: 기존 섹터 내에서의 큰 변화, 유망 밸류체인(소부장) 발견, 핵심 부품의 구조적 수요 증가.
- 4~6: 일반적인 실적 발표, 누구나 아는 대기업(애플, 삼성 등)의 뻔한 뉴스. (점수 낮게 부여)
- 1~3: 가십, 이미 시장에 선반영된 뉴스.

반드시 여러 뉴스가 주어질 때 JSON 배열 `[{...}, {...}]` 형태로만 응답하세요.
"""

# ============================================================
# Agent 3: Validator 설정 (한국 반영 검증)
# ============================================================
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
KOREA_REFLECTED_THRESHOLD = 3  # 네이버 뉴스 검색 결과가 이 수 이상이면 '반영됨' 판정

# ============================================================
# Pipeline 설정
# ============================================================
PIPELINE_INTERVAL_MINUTES = 30  # 파이프라인 실행 간격
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# Server 설정
# ============================================================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8899
