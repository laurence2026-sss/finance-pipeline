
import os
from dotenv import load_dotenv
from google import genai

# .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 에러: .env 파일에 GEMINI_API_KEY가 없습니다.")
    exit(1)

print(f"📡 테스트 시작 (Key: {api_key[:10]}...)")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hello, are you working?"
    )
    print("✅ 성공! Gemini 응답:")
    print("-" * 30)
    print(response.text)
    print("-" * 30)
except Exception as e:
    print("❌ 실패! 상세 에러:")
    print(e)
