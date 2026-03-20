# 🚀 Intelligence Pipeline Project Guide

## 1. 프로젝트 목표 (Objective)
- **최종형태**: GitHub Actions에서 2시간 주기로 자동 실행되는 뉴스/자본 분석 파이프라인.
- **핵심가치**: 한국 언론 미반영(Alpha) 및 7점 이상의 상급 정보(Mainstream) 필터링.
- **알림**: 고득점 독점 정보를 텔레그램으로 실시간 수신.

## 2. 현재 진행 상황 (Current Status)
- **Engine**: Groq (Llama 3.3 70B) 기반 분석/요약 엔진 탑재.
- **Infrastructure**: GitHub Actions 연동 완료 (Secrets/Write 권한 설정 완료).
- **Automation**: 매일 2시간마다 전 섹터(AI, 포토닉스, 우주, 로보틱스, 큰손) 감시 가동 중.
- **Dashboard**: [🚨 미반영 독점] vs [📌 기반영 핵심(7점↑)] 탭 구조로 개편 완료.

## 3. ⚠️ 절대 수정 및 변경 금지 (Mandatory Guidelines)
- **Environment**: `.env` 내 `GROQ_API_KEY` (대문자) 명칭 및 연동 구조 유지. 
- **Architecture**: `Collector` -> `Filter` -> `Validator` -> `Notifier` 4단계 파이프라인 구조 변경 금지.
- **Logic**: `validator.py`의 네이버 뉴스 검색 기반 '독점/초동/기반영' 판정 알고리즘 보호.
- **Config**: `VOLUME_SPIKE_THRESHOLD = 2.5` (기관 매집 감지 임계치) 하향 절대 금지.

## 4. 폴더 및 파일 구성
- `pipeline.py`: 중앙 컨트롤러 (실물 실행 파일).
- `agents/`: 각 단계별 에이전트 (filter, validator, notifier, collector).
- `config.py`: 모든 티커(NVDA, RKLB 등), RSS 주소, 임계치 설정.
- `intelligence_dashboard/`: 탭 구조가 도입된 HTML/JS 대시보드.
- `data/`: 분석 결과 JSON 파일 저장소.
