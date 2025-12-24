"""
Query Intent Parser

자연어 쿼리에서 분석 의도를 파악합니다.

사용법:
    parser = QueryIntentParser(llm)
    intent = parser.parse("12월 20일 기준으로 삼성전자 투자해도 될까?")
    
    # 결과:
    # {
    #     "target_companies": ["삼성전자"],
    #     "target_date": "2024-12-20",
    #     "intent": "investment_recommendation",
    #     "original_query": "...",
    #     "document_path": None
    # }
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class QueryIntentParser:
    """
    자연어 쿼리에서 분석 의도 추출
    
    추출 항목:
    - target_companies: 분석 대상 기업
    - target_date: 분석 기준일
    - intent: 쿼리 의도 (investment, analysis, comparison 등)
    - document_path: 첨부 문서 경로 (있는 경우)
    """
    
    # 알려진 기업명 (확장 가능)
    KNOWN_COMPANIES = [
        "삼성전자", "SK하이닉스", "LG전자", "네이버", "카카오",
        "현대차", "기아", "삼성SDI", "LG에너지솔루션", "포스코홀딩스",
        "삼성바이오로직스", "셀트리온", "KB금융", "신한지주", "하나금융"
    ]
    
    # 의도 키워드 매핑
    INTENT_KEYWORDS = {
        "investment_recommendation": ["투자", "사도 될", "매수", "살까", "괜찮을까", "어때"],
        "sell_recommendation": ["팔까", "매도", "손절", "익절"],
        "analysis": ["분석", "전망", "현황", "상황"],
        "comparison": ["비교", "차이", "vs", "대비"]
    }
    
    def __init__(self, llm=None):
        """
        Args:
            llm: LangChain LLM (없으면 규칙 기반으로만 동작)
        """
        self.llm = llm
    
    def parse(self, query: str, document_path: Optional[str] = None) -> Dict[str, Any]:
        """
        자연어 쿼리 파싱
        
        Args:
            query: 사용자 자연어 쿼리
            document_path: 첨부 문서 경로 (선택)
            
        Returns:
            파싱 결과 딕셔너리
        """
        result = {
            "original_query": query,
            "target_companies": [],
            "target_date": None,
            "intent": "analysis",  # 기본값
            "document_path": document_path
        }
        
        # 1. 기업명 추출
        result["target_companies"] = self._extract_companies(query)
        
        # 2. 날짜 추출
        result["target_date"] = self._extract_date(query)
        
        # 3. 의도 추출
        result["intent"] = self._extract_intent(query)
        
        # 4. LLM으로 보완 (옵션)
        if self.llm and not result["target_companies"]:
            result = self._enhance_with_llm(query, result)
        
        # 5. 기본값 설정
        if not result["target_date"]:
            result["target_date"] = datetime.now().strftime("%Y-%m-%d")
        
        return result
    
    def _extract_companies(self, query: str) -> List[str]:
        """기업명 추출 (규칙 기반)"""
        companies = []
        for company in self.KNOWN_COMPANIES:
            if company in query:
                companies.append(company)
        return companies
    
    def _extract_date(self, query: str) -> Optional[str]:
        """날짜 추출 (정규식 기반)"""
        current_year = datetime.now().year
        
        # 패턴 1: "12월 20일", "12/20"
        match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', query)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            return f"{current_year}-{month:02d}-{day:02d}"
        
        match = re.search(r'(\d{1,2})/(\d{1,2})', query)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            return f"{current_year}-{month:02d}-{day:02d}"
        
        # 패턴 2: "2024-12-20", "2024.12.20"
        match = re.search(r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})', query)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return f"{year}-{month:02d}-{day:02d}"
        
        # 패턴 3: "오늘", "어제", "지난주"
        if "오늘" in query:
            return datetime.now().strftime("%Y-%m-%d")
        if "어제" in query:
            return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if "지난주" in query:
            return (datetime.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")
        
        return None
    
    def _extract_intent(self, query: str) -> str:
        """의도 추출 (키워드 기반)"""
        query_lower = query.lower()
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return intent
        
        return "analysis"  # 기본값
    
    def _enhance_with_llm(self, query: str, result: Dict, document_content: str = None) -> Dict:
        """LLM으로 파싱 결과 보완 (prompts.yaml 템플릿 사용)"""
        if not self.llm:
            return result
        
        try:
            from src.config.prompt_loader import PROMPTS
            
            # prompts.yaml에서 query_parser 템플릿 로드
            template = PROMPTS.get("query_parser", {}).get("instruction", "")
            
            if template:
                prompt = template.format(
                    query=query,
                    document_content=document_content or "없음"
                )
            else:
                # Fallback 프롬프트
                prompt = f"""
다음 한국어 금융 분석 쿼리에서 정보를 추출하세요.

쿼리: "{query}"
첨부 문서: {document_content or "없음"}

JSON 형식으로 응답:
{{
    "companies": ["기업명1", "기업명2"],
    "date": "YYYY-MM-DD 또는 null",
    "intent": "investment_recommendation | sell_recommendation | analysis | comparison",
    "document_summary": "문서 핵심 요약 (없으면 null)"
}}

주의: 기업명은 한국 상장사만 추출. 날짜가 명시되지 않으면 null.
"""
            
            response = self.llm.invoke(prompt)
            import json
            content = response.content if hasattr(response, 'content') else str(response)
            
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                if parsed.get("companies"):
                    result["target_companies"] = parsed["companies"]
                if parsed.get("date"):
                    result["target_date"] = parsed["date"]
                if parsed.get("intent"):
                    result["intent"] = parsed["intent"]
                if parsed.get("document_summary"):
                    result["document_summary"] = parsed["document_summary"]
        except Exception as e:
            print(f"[경고] LLM 파싱 실패: {e}")
        
        return result
    
    def parse_document(self, document_content: str) -> Dict[str, Any]:
        """
        문서 내용 분석 (prompts.yaml document_summary 템플릿 사용)
        
        Args:
            document_content: 문서 텍스트 내용
            
        Returns:
            문서 분석 결과 딕셔너리
        """
        if not self.llm:
            return {"error": "LLM이 초기화되지 않았습니다."}
        
        try:
            from src.config.prompt_loader import PROMPTS
            
            template = PROMPTS.get("document_summary", {}).get("instruction", "")
            
            if template:
                prompt = template.format(document_content=document_content[:5000])  # 토큰 제한
            else:
                prompt = f"다음 문서를 요약하세요:\n\n{document_content[:3000]}"
            
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            
            return {"summary": content}
        except Exception as e:
            return {"error": str(e)}


def parse_query(query: str, llm=None, document_path: str = None) -> Dict[str, Any]:
    """간편 함수"""
    parser = QueryIntentParser(llm)
    return parser.parse(query, document_path)


# 테스트
if __name__ == "__main__":
    test_queries = [
        "삼성전자 투자해도 될까?",
        "12월 20일 기준으로 SK하이닉스 분석해줘",
        "오늘 기준 네이버랑 카카오 비교해줘",
        "2024년 11월 15일 LG전자 매수할까?",
    ]
    
    parser = QueryIntentParser()
    
    for q in test_queries:
        result = parser.parse(q)
        print(f"\n쿼리: {q}")
        print(f"  기업: {result['target_companies']}")
        print(f"  날짜: {result['target_date']}")
        print(f"  의도: {result['intent']}")
