"""
Pipeline Orchestrator
======================
3단계 에이전트 파이프라인을 순차적으로 실행합니다.
Collector → Filter → Validator
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from agents.collector import run_collector
from agents.filter import run_filter
from agents.validator import run_validator
from agents.notifier import run_notifier
from config import DATA_DIR, NOTIFY_THRESHOLD


def run_pipeline():
    """
    전체 파이프라인을 1회 실행합니다.
    
    1. Agent 1 (Collector): 소스에서 Raw Data 수집
    2. Agent 2 (Filter): 노이즈 제거 및 영향도 채점
    3. Agent 3 (Validator): 한국 뉴스 반영 여부 확인
    """
    start_time = datetime.now()
    
    print("\n" + "🚀" * 30)
    print(f"  GLOBAL INTELLIGENCE PIPELINE")
    print(f"  시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🚀" * 30 + "\n")
    
    # Stage 1: 수집
    raw_items = run_collector()
    
    if not raw_items:
        print("\n❌ 수집된 데이터가 없습니다. 네트워크 연결을 확인하세요.")
        return []
    
    # Stage 2: 필터링
    print()
    filtered_items = run_filter(raw_items)
    
    if not filtered_items:
        print("\n⚠️ 임계값을 통과한 정보가 없습니다. 임계값을 낮춰보세요.")
        return []
    
    # Stage 3: 한국 반영 검증
    print()
    final_items = run_validator(filtered_items)
    
    # Stage 4: 텔레그램 알림 (9점 이상 핵심 정보만)
    print()
    run_notifier(final_items, threshold=NOTIFY_THRESHOLD)
    
    # 실행 메타데이터 저장
    elapsed = (datetime.now() - start_time).total_seconds()
    meta = {
        "last_run": start_time.isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "raw_count": len(raw_items),
        "filtered_count": len(filtered_items),
        "final_count": len(final_items),
        "exclusive_count": sum(1 for i in final_items if "독점" in i.get("korea_status", "")),
        "early_count": sum(1 for i in final_items if "초기" in i.get("korea_status", "")),
        "reflected_count": sum(1 for i in final_items if "이미" in i.get("korea_status", "")),
    }
    
    meta_path = os.path.join(DATA_DIR, "pipeline_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # 최종 보고
    print("\n" + "=" * 60)
    print("📊 PIPELINE 완료 보고")
    print("=" * 60)
    print(f"  ⏱️  소요 시간: {elapsed:.1f}초")
    print(f"  📡 수집: {meta['raw_count']}건")
    print(f"  🔍 필터 통과: {meta['filtered_count']}건")
    print(f"  🔥 독점 정보: {meta['exclusive_count']}건")
    print(f"  ⚡ 초기 반영: {meta['early_count']}건")
    print(f"  ⚪ 이미 반영: {meta['reflected_count']}건")
    print("=" * 60)
    
    return final_items


if __name__ == "__main__":
    results = run_pipeline()
