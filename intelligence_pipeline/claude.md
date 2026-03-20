# 🚀 Intelligence Pipeline Project Guide

## 1. 프로젝트 목표 (Objective)
- **안정성**: 기술/자금 흐름 포착을 위한 결함 없는 파이프라인 설계 및 유지.
- **자동화**: GitHub Actions를 통한 주기적 실행 체계 구축.
- **전달**: 고가치 정보(Exclusive/Early) 선별 후 텔레그램 실시간 문자 발송.

## 2. 현재 진행 현황 (Current Status)
- **Engine**: Groq (Llama 3.3 70B) 기반 정밀 분석 및 뉴스 가치 채점 가동 중.
- **Validation**: 네이버 뉴스 API를 이용한 한국 시장 선반영 여부(독점/초동/기반영) 검증 완료.
- **Topics**: AI 하드웨어, 포토닉스, 우주 인프라, 로보틱스, 월가 큰손(Whales/Insider) 트래킹 추가 완료.

## 3. ⚠️ 절대 수정 및 변경 금지 (Mandatory Guidelines)
- **API Key Naming**: `.env` 및 `config.py` 내 `GROQ_API_KEY` 명칭(대문자) 절대 유지.
- **Pipeline Structure**: `Collector` -> `Filter` -> `Validator` -> `Notifier` 4단계 구조 불변.
- **Volume Spike**: `config.py`의 `VOLUME_SPIKE_THRESHOLD = 2.5` 비율은 기관 자금 포착 임계치이므로 임의 하향 금지.
- **Korean Logic**: `validator.py`의 키워드 매핑 및 검색 쿼리 생성 로직 보호.

## 4. 파일 경로 가이드
- **메인 실행**: `pipeline.py`
- **에이전트**: `agents/` (filter, validator, notifier, collector)
- **설정**: `config.py`, `.env`
- **데이터**: `data/` (raw, filtered, validated JSON)
