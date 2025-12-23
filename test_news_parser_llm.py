"""News Parser LLM 응답 디버깅 스크립트"""
import os
import json
from pathlib import Path

# API 키 확인
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f"API Key 존재: {bool(api_key)}")
print(f"API Key 앞 10자: {api_key[:10] if api_key else 'N/A'}...")

# Google Genai SDK 테스트
try:
    from google import genai
    from google.genai import types
    print("✅ google-genai 라이브러리 임포트 성공")
except ImportError as e:
    print(f"❌ google-genai 임포트 실패: {e}")
    exit(1)

# KG Schema 로드
try:
    from src.models.nodes import get_kg_json_schema
    schema = get_kg_json_schema()
    print(f"✅ KG JSON Schema 로드 성공")
except Exception as e:
    print(f"❌ Schema 로드 실패: {e}")
    schema = None

# 프롬프트 로드
try:
    from src.config.prompt_loader import PROMPTS
    prompt_tmpl = PROMPTS.get('news_parser', {}).get('kg_extraction', {}).get('instruction', '')
    print(f"✅ 프롬프트 로드 성공 (길이: {len(prompt_tmpl)}자)")
except Exception as e:
    print(f"❌ 프롬프트 로드 실패: {e}")
    prompt_tmpl = ""

# 테스트 뉴스 텍스트
test_news = """
[뉴스 1]
날짜: 2020-01-10
제목: 삼성전자, HBM3E 양산 본격화...SK하이닉스 추격
본문: 삼성전자가 고대역폭메모리(HBM) 3E 양산을 본격화한다. 업계에서는 SK하이닉스를 추격하기 위한 삼성의 전략으로 분석했다.
키워드: 삼성전자, HBM
"""

if prompt_tmpl:
    full_prompt = prompt_tmpl.format(news_text=test_news)
else:
    full_prompt = f"""
    뉴스에서 영향받는 기업을 추출하세요:
    {test_news}
    
    JSON 형식으로 반환:
    {{"entities": ["삼성전자", "SK하이닉스"], "relations": []}}
    """

print(f"\n📝 프롬프트 길이: {len(full_prompt)}자")
print(f"📝 프롬프트 앞 500자:\n{full_prompt[:500]}...")

# Gemini API 호출
print("\n🔄 Gemini API 호출 중...")
try:
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": [{"text": full_prompt}]}],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema
        ) if schema else None
    )
    
    print(f"\n✅ API 호출 성공!")
    print(f"응답 타입: {type(response)}")
    print(f"response.text 타입: {type(response.text)}")
    print(f"response.text 내용 (첫 500자):")
    print(response.text[:500] if response.text else "EMPTY")
    
    # JSON 파싱 시도
    try:
        kg_json = json.loads(response.text)
        print(f"\n✅ JSON 파싱 성공!")
        print(f"entities 수: {len(kg_json.get('entities', []))}")
        print(f"relations 수: {len(kg_json.get('relations', []))}")
        print(f"\n샘플 entities:")
        for e in kg_json.get('entities', [])[:5]:
            print(f"  - {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 파싱 실패: {e}")
        print(f"원본 응답:\n{response.text[:1000]}")
        
except Exception as e:
    print(f"\n❌ API 호출 실패: {e}")
    import traceback
    traceback.print_exc()
