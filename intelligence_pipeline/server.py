"""
FastAPI Server
===============
대시보드에 데이터를 제공하는 API 서버입니다.
파이프라인 실행 및 결과 조회를 지원합니다.
"""

import json
import os
import sys
import threading
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config import DATA_DIR, SERVER_HOST, SERVER_PORT
from pipeline import run_pipeline

app = FastAPI(title="Intelligence Pipeline API", version="1.0")

# CORS 허용 (대시보드에서 접근)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 대시보드 정적 파일 서빙
dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "intelligence_dashboard")
if os.path.exists(dashboard_dir):
    app.mount("/static", StaticFiles(directory=dashboard_dir), name="dashboard")


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """대시보드 메인 페이지"""
    index_path = os.path.join(dashboard_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Intelligence Pipeline API — /docs 에서 API 문서 확인"}


@app.get("/api/intelligence")
async def get_intelligence():
    """최종 인텔리전스 데이터 조회"""
    path = os.path.join(DATA_DIR, "final_intelligence.json")
    if not os.path.exists(path):
        return {"items": [], "message": "파이프라인을 먼저 실행하세요."}
    
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    return {"items": items, "count": len(items)}


@app.get("/api/raw")
async def get_raw():
    """Raw 수집 데이터 조회"""
    path = os.path.join(DATA_DIR, "raw_intelligence.json")
    if not os.path.exists(path):
        return {"items": [], "message": "데이터 없음"}
    
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    
    return {"items": items, "count": len(items)}


@app.get("/api/meta")
async def get_meta():
    """파이프라인 실행 메타데이터 조회"""
    path = os.path.join(DATA_DIR, "pipeline_meta.json")
    if not os.path.exists(path):
        return {"message": "파이프라인을 먼저 실행하세요."}
    
    with open(path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    return meta


@app.post("/api/run")
async def trigger_pipeline():
    """파이프라인 수동 실행 트리거"""
    def _run_in_background():
        try:
            run_pipeline()
        except Exception as e:
            print(f"[Server] 파이프라인 실행 에러: {e}")
    
    thread = threading.Thread(target=_run_in_background, daemon=True)
    thread.start()
    
    return {"message": "파이프라인 실행 시작됨", "started_at": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    print(f"\n🖥️  대시보드 서버 시작: http://localhost:{SERVER_PORT}")
    print(f"📊 대시보드: http://localhost:{SERVER_PORT}/")
    print(f"📡 API 문서: http://localhost:{SERVER_PORT}/docs\n")
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
