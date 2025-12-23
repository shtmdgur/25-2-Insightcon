"""
News Parser Agent

뉴스 CSV 파일에서 이벤트를 추출하여 Knowledge Graph로 변환합니다.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd
from datetime import datetime

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType
from src.dataflows.event_extractor import EventExtractor

logger = logging.getLogger(__name__)


class NewsParserAgent(BaseParserAgent):
    """
    뉴스 이벤트 추출 Agent
    
    데이터 레이어: 100% 동적 (Event)
    Neo4j 전략: CREATE (시간 속성 필수)
    """
    
    def __init__(self, llm=None, use_batch: bool = False):
        """
        Args:
            llm: LLM 모델 (EventExtractor용)
            use_batch: Batch API 사용 여부
        """
        super().__init__(name="NewsParserAgent")
        self.llm = llm
        self.use_batch = use_batch
        self.event_extractor = EventExtractor(llm, neo4j_client=None) if llm else None
    
    def parse(
        self, 
        file_path: Path, 
        output_dir: Path = None,
        skip_existing: bool = False
    ) -> KnowledgeGraph:
        """
        뉴스 CSV를 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: CSV 파일 경로 (Semiconductor_News_Raw_*.csv)
            output_dir: 개별 JSON 저장 디렉토리 (기본: data/processed)
            skip_existing: 이미 저장된 행은 건너뛰기
        
        Returns:
            KnowledgeGraph 객체 (Event 노드)
        
        Raises:
            ValueError: CSV 파싱 실패 시
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.csv':
            raise ValueError(f"Not a CSV file: {file_path}")
        
        try:
            self.logger.info(f"Parsing news CSV: {file_path}")
            
            # CSV 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 검증
            self._validate_columns(df)
            
            # Knowledge Graph 생성 (개별 저장 모드)
            kg = self._create_knowledge_graph(df, file_path, output_dir, skip_existing)
            
            self.logger.info(
                f"News CSV parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse news CSV {file_path}: {str(e)}")
            raise ValueError(f"News CSV parsing failed: {str(e)}")
    
    def batch_parse(
        self, 
        csv_files: list, 
        output_dir: Path,
        skip_existing: bool = False
    ) -> dict:
        """
        여러 뉴스 CSV 파일 배치 파싱 (KGConstructionAgent 호환용)
        
        Args:
            csv_files: CSV 파일 경로 리스트
            output_dir: 결과 JSON 저장 디렉토리
            skip_existing: 이미 결과 파일이 존재하면 건너뛰기
        
        Returns:
            파싱 결과 통계 {'total': int, 'success': int, 'failed': int}
        """
        result = {'total': 0, 'success': 0, 'failed': 0}
        
        for csv_file in csv_files:
            csv_path = Path(csv_file)
            result['total'] += 1
            
            # 출력 파일 경로 (전체 CSV 병합 결과)
            output_file = output_dir / f"{csv_path.stem}_kg.json"
            
            # 건너뛰기 체크 (전체 CSV 결과 기준)
            if skip_existing and output_file.exists():
                self.logger.info(f"Skipping existing News KG: {output_file.name}")
                result['success'] += 1
                continue
            
            try:
                # 파싱 실행 (개별 행 저장 포함)
                kg = self.parse(csv_path, output_dir, skip_existing)
                
                # 전체 병합 결과 JSON 저장
                kg.save_to_json(str(output_file))
                self.logger.info(f"Saved News KG to: {output_file}")
                
                result['success'] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to parse {csv_path.name}: {e}")
                result['failed'] += 1
        
        return result
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        if "entities" not in data or "relations" not in data:
            self.logger.warning("Missing entities or relations")
            return False
        
        # Issue 엔티티 확인
        has_issues = any(
            e.get("type") == NodeType.ISSUE.value
            for e in data["entities"]
        )
        
        if not has_issues:
            self.logger.warning("No Issue entities found")
            return False
        
        return True
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        CSV 필수 컬럼 검증
        
        Args:
            df: DataFrame
        
        Raises:
            ValueError: 필수 컬럼 누락 시
        """
        columns_lower = [col.lower() for col in df.columns]
        
        required = ["title", "date"]
        missing = [col for col in required if col not in columns_lower]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        if len(df) == 0:
            raise ValueError("CSV file is empty")
    
    def _create_knowledge_graph(
        self,
        df: pd.DataFrame,
        file_path: Path,
        output_dir: Path = None,
        skip_existing: bool = False
    ) -> KnowledgeGraph:
        """
        DataFrame의 모든 행을 개별적으로 처리하여 Knowledge Graph로 변환 (v3.4)
        각 행마다 개별 JSON 파일로 저장하여 중단 시 재개 가능
        """
        import json
        import os
        from google import genai
        from google.genai import types
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from src.models.nodes import get_kg_json_schema, KnowledgeGraph
        from src.utils.entity_matcher import EntityMatcher
        
        # 컬럼명 정규화 및 날짜 처리
        df.columns = [col.lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()].sort_values('date', ascending=False)
        
        # 설정 로드
        from src.config.parser_config import get_config
        config = get_config('news')
        sample_size = min(config.sample_size, len(df))
        sampled_df = df.head(sample_size)
        
        self.logger.info(f"뉴스 처리 시작: 총 {len(sampled_df)}행 (개별 파싱, 개별 저장)")
        
        normalizer = EntityMatcher()
        final_kg = KnowledgeGraph()
        
        # 출력 디렉토리 설정 (news_rows 서브폴더)
        if output_dir is None:
            output_dir = Path("data/processed")
        news_output_dir = output_dir / "news_rows"
        news_output_dir.mkdir(parents=True, exist_ok=True)
        
        # YAML에서 프롬프트 로드
        from src.config.prompt_loader import PROMPTS
        prompt_tmpl = PROMPTS.get('news_parser', {}).get('kg_extraction', {}).get('instruction', '')
        
        if not prompt_tmpl or not self.llm:
            self.logger.warning("LLM 또는 프롬프트 누락으로 수동 폴백 실행")
            return self._create_kg_manual_fallback(sampled_df, file_path)

        def process_and_save_row(row_idx, row):
            """각 행을 처리하고 개별 JSON으로 저장"""
            # 개별 파일 경로 생성 (CSV명_행번호_날짜.json)
            date_str = row['date'].strftime('%Y-%m-%d')
            row_output_file = news_output_dir / f"{file_path.stem}_row{row_idx}_{date_str}_kg.json"
            
            # skip_existing 체크
            if skip_existing and row_output_file.exists():
                try:
                    existing_kg = KnowledgeGraph.load_from_json(str(row_output_file))
                    return existing_kg, "skipped"
                except Exception:
                    pass  # 파일 손상 시 재처리
            
            try:
                title = str(row.get('title', ''))[:config.max_title_length]
                # content가 없으면 description 사용
                content = str(row.get('content', row.get('description', ''))).strip()[:1000]
                keyword = str(row.get('keyword', '')).strip()
                
                news_text = f"날짜: {date_str}\n제목: {title}\n본문: {content}\n키워드: {keyword}"
                full_prompt = prompt_tmpl.format(news_text=news_text)
                
                from src.config.llm_config import get_model
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
                response = client.models.generate_content(
                    model=get_model("news_parsing"),
                    contents=[{"role": "user", "parts": [{"text": full_prompt}]}],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=get_kg_json_schema()
                    )
                )
                
                kg_dict = json.loads(response.text)
                row_kg = KnowledgeGraph.from_gemini_dict(kg_dict)
                
                # 정규화
                for entity in row_kg.entities:
                    entity.name = normalizer.match(entity.name)
                    entity.properties['source_date'] = date_str
                    entity.properties['source_row'] = row_idx
                for rel in row_kg.relations:
                    rel.subject = normalizer.match(rel.subject)
                    rel.object = normalizer.match(rel.object)
                    rel.date = date_str
                
                # 메타데이터 추가
                row_kg.metadata = {
                    "source_file": str(file_path),
                    "row_index": row_idx,
                    "date": date_str,
                    "title": title[:100]
                }
                
                # 개별 JSON 저장
                row_kg.save_to_json(str(row_output_file))
                
                return row_kg, "success"
            except Exception as e:
                self.logger.error(f"행 {row_idx} 처리 실패: {e}")
                return None, "failed"

        # 병렬 처리 (속도 향상을 위해 5개씩 병렬 실행)
        success_count = 0
        fail_count = 0
        skipped_count = 0
        total = len(sampled_df)
        
        self.logger.info(f"📰 뉴스 LLM 파싱 시작 (max_workers=5, 총 {total}건, 개별 저장: {news_output_dir})")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_row = {
                executor.submit(process_and_save_row, i, row): i 
                for i, row in sampled_df.iterrows()
            }
            
            processed_count = 0
            for future in as_completed(future_to_row):
                processed_count += 1
                try:
                    row_kg, status = future.result()
                    if status == "success":
                        final_kg.merge(row_kg)
                        success_count += 1
                    elif status == "skipped":
                        if row_kg:
                            final_kg.merge(row_kg)
                        skipped_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    fail_count += 1
                    self.logger.error(f"뉴스 행 처리 예외: {e}")
                
                # 5건마다 진행 로그
                if processed_count % 5 == 0 or processed_count == total:
                    self.logger.info(f"📰 뉴스 진행: {processed_count}/{total} (성공: {success_count}, 스킵: {skipped_count}, 실패: {fail_count})")

        # 메타데이터 보강
        final_kg.metadata = {
            "source_file": str(file_path),
            "total_rows": len(df),
            "processed_rows": len(sampled_df),
            "success_count": success_count,
            "skipped_count": skipped_count,
            "failed_count": fail_count,
            "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}",
            "mode": "row_by_row_individual_save",
            "output_dir": str(news_output_dir)
        }
        
        self.logger.info(f"📰 뉴스 파싱 완료: 개별 JSON {success_count + skipped_count}개 저장됨 ({news_output_dir})")
        
        return final_kg
    
    def _create_kg_manual_fallback(
        self,
        df: pd.DataFrame,
        file_path: Path
    ) -> KnowledgeGraph:
        """
        LLM 실패 시 수동 KG 생성 (기존 로직 보존)
        """
        from src.config.parser_config import get_config
        config = get_config('news')
        
        entities = []
        relations = []
        
        for idx, row in df.iterrows():
            date_str = row['date'].strftime('%Y-%m-%d')
            title = str(row.get('title', ''))[:config.max_title_length]
            keyword = str(row.get('keyword', '')).strip()
            
            # Issue 엔티티 생성
            title_short = self._extract_issue_keyword(title)
            issue_name = f"Issue_{title_short}_{date_str}"
            
            issue_entity = Entity(
                name=issue_name,
                type=NodeType.ISSUE,
                sentiment=self._classify_sentiment(title),
                properties={
                    "date": date_str,
                    "title": title,
                    "keyword": keyword,
                    "link": str(row.get('link', '')),
                    "time_decay_weight": self._calculate_time_decay(date_str)
                },
                confidence=0.8
            )
            entities.append(issue_entity)
            
            # keyword 기반 관계 생성
            if keyword:
                from src.utils.ticker_mapping import resolve_entity_name, get_node_type
                keywords = [k.strip() for k in keyword.split(',') if k.strip()]
                
                for k in keywords:
                    if self._is_invalid_company_name(k):
                        continue
                    normalized_keyword = resolve_entity_name(k)
                    node_type = get_node_type(normalized_keyword)
                    
                    agent_entity = Entity(
                        name=normalized_keyword,
                        type=node_type,
                        confidence=0.6
                    )
                    entities.append(agent_entity)
                    
                    relation = Relation(
                        subject=normalized_keyword,
                        predicate=RelationType.HAS_SIGNAL,
                        object=issue_entity.name,
                        date=date_str,
                        source=title,
                        properties={"weight": issue_entity.properties['time_decay_weight']}
                    )
                    relations.append(relation)
        
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_file": str(file_path),
                "file_type": "news_csv",
                "total_news": len(df),
                "extraction_method": "manual_fallback"
            }
        )
        
        return kg

    
    def _calculate_time_decay(self, event_date: str) -> float:
        """
        시간 감쇠 가중치 계산
        
        Args:
            event_date: 이벤트 날짜 (YYYY-MM-DD)
        
        Returns:
            감쇠 가중치 (0.1~1.0)
        """
        try:
            import numpy as np
            from src.config.parser_config import get_config
            
            config = get_config('news')
            event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            current_dt = datetime.now()
            
            days_diff = (current_dt - event_dt).days
            
            # 반감기 (config에서 가져옴)
            decay_factor = np.exp(-days_diff / config.time_decay_halflife)
            
            # 최소 가중치
            return max(decay_factor, config.time_decay_min_weight)
            
        except Exception as e:
            self.logger.warning(f"Time decay calculation failed: {str(e)}")
            return 0.5  # 기본값
    
    def _classify_sentiment(self, title: str) -> str:
        """
        뉴스 제목 기반 Sentiment 분류
        
        Args:
            title: 뉴스 제목
        
        Returns:
            "POSITIVE" | "NEGATIVE" | "NEUTRAL"
        """
        positive_keywords = ["성장", "증가", "확대", "투자", "개발", "성공", "호조", "상승", "수주"]
        negative_keywords = ["감소", "하락", "적자", "위기", "손실", "축소", "악화", "하향", "부진"]
        
        title_lower = title.lower()
        for keyword in positive_keywords:
            if keyword in title_lower:
                return "POSITIVE"
        for keyword in negative_keywords:
            if keyword in title_lower:
                return "NEGATIVE"
        return "NEUTRAL"
    
    def _extract_issue_keyword(self, title: str) -> str:
        """
        뉴스 제목에서 의미있는 키워드 추출
        
        Args:
            title: 뉴스 제목
        
        Returns:
            정제된 키워드 (최대 30자)
        """
        import re
        
        # 대괄호 내용 제거 (예: [주가동향], [이데일리], [머니투데이])
        cleaned = re.sub(r'\[.*?\]', '', title)
        # 특수문자 제거
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        # 중복 공백 제거 및 앞뒤 공백 제거
        cleaned = ' '.join(cleaned.split()).strip()
        
        # 최대 30자로 제한 (Neo4j 속성 이름으로 적합하게)
        if len(cleaned) > 30:
            cleaned = cleaned[:30].rsplit(' ', 1)[0]  # 단어 중간에서 자르지 않음
        
        return cleaned if cleaned else "Unknown"
    
    def _extract_text_from_response(self, content) -> str:
        """
        LLM 응답에서 순수 텍스트 추출 (다양한 형태 처리)
        
        Gemini API 응답이 list, dict, object 등 다양한 형태로 올 수 있음
        """
        import re
        
        if content is None:
            return ""
        
        # 이미 문자열인 경우
        if isinstance(content, str):
            return content.strip()
        
        # list인 경우
        if isinstance(content, list):
            if not content:
                return ""
            first_item = content[0]
            
            # 객체에서 text 속성 추출
            if hasattr(first_item, 'text'):
                return first_item.text.strip()
            
            # dict에서 text 키 추출 (LangChain 형식)
            if isinstance(first_item, dict):
                if 'text' in first_item:
                    return first_item['text'].strip()
                # type이 'text'인 경우의 text 값 추출
                if first_item.get('type') == 'text' and 'text' in first_item:
                    return first_item['text'].strip()
            
            # 문자열인 경우
            if isinstance(first_item, str):
                return first_item.strip()
            
            # 기타: 문자열 변환 후 text 값만 추출
            text_str = str(first_item)
            # "'text': 'SK하이닉스'" 형태에서 실제 값 추출
            match = re.search(r"'text':\s*'([^']*)'", text_str)
            if match:
                return match.group(1).strip()
            
            # "text: SK하이닉스" 형태 처리
            match = re.search(r"text:\s*(.+)", text_str)
            if match:
                return match.group(1).strip()
            
            # 최후의 수단: 전체 문자열 반환
            self.logger.debug(f"Could not extract text from list item: {type(first_item)} - {text_str[:100]}")
            return text_str
        
        # dict인 경우
        if isinstance(content, dict):
            if 'text' in content:
                return content['text'].strip()
            return str(content).strip()
        
        # 객체인 경우 (AIMessage 등)
        if hasattr(content, 'text'):
            return content.text.strip()
        
        # 문자열인 경우 그대로 반환
        if isinstance(content, str):
            return content.strip()
        
        return str(content).strip()
    
    def _is_invalid_company_name(self, name: str) -> bool:
        """
        잘못된 회사명 필터링 (파싱 오류 결과물 및 불용어)
        """
        invalid_patterns = [
            "'text':", "text:", "{", "}", "[", "]", ":", 
            "있습니다", "하는", "했다", "라며", "대로", "부터", "까지",
            "라는", "보다", "위한", "통해", "대한", "전년", "대기", "이상"
        ]
        
        # 특수문자만 있거나 너무 긴 경우 (문장 오인)
        import re
        if len(name) > 20 and ' ' in name:
            return True
            
        return any(pattern in name for pattern in invalid_patterns) or len(name) < 2
    
    def _extract_affected_entities(
        self,
        title: str,
        description: str,
        keyword: str
    ) -> List[str]:
        """
        LLM으로 뉴스에서 영향받는 기업/엔티티 추출
        
        Args:
            title: 뉴스 제목
            description: 뉴스 본문
            keyword: 뉴스 키워드
        
        Returns:
            영향받는 기업 리스트 (정규화된 이름)
        """
        if not self.llm:
            return [keyword] if keyword else []
        
        try:
            # 1. YAML에서 전문 프롬프트 로드 시도
            from src.config.prompt_loader import PROMPTS
            prompt_tmpl = PROMPTS.get('news_parser', {}).get('kg_extraction', {}).get('instruction', '')
            
            if prompt_tmpl:
                prompt = prompt_tmpl.format(news_text=f"제목: {title}\n본문: {description}\n키워드: {keyword}")
            else:
                # 2. Fallback: 기존 하드코딩 프롬프트 (최소한의 동작 보장)
                prompt = f"""
다음 뉴스에서 영향을 받는 기업/회사 이름을 추출하세요.

제목: {title}
본문: {description}
키워드: {keyword}

**규칙**:
1. 기업명만 추출 (개인, 제품, 기술 제외)
2. 정식 명칭 사용 (예: "삼성" → "삼성전자")
3. 최대 3개 기업
4. 쉼표로 구분

예시 출력: "삼성전자, SK하이닉스, TSMC"

추출 결과:
"""
            
            response = self.llm.invoke(prompt)
            
            # LLM 응답에서 텍스트 추출
            extracted_text = self._extract_text_from_response(response.content)
            
            # 디버그: LLM 응답 원본 로깅
            self.logger.debug(f"LLM raw response type: {type(response.content)}")
            self.logger.debug(f"Extracted text (first 200 chars): {extracted_text[:200] if extracted_text else 'EMPTY'}")
            
            # JSON 파싱 시도 (v3.3: 디버깅 강화)
            import json
            import re
            
            companies = []
            
            # 0. 마크다운 코드블록 제거 (```json ... ``` 형태)
            cleaned_text = re.sub(r'```(?:json)?\s*', '', extracted_text)
            cleaned_text = re.sub(r'```', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            # 1. JSON 형태인 경우 ({ "entities": [...] } 또는 [ "A", "B" ])
            json_match = re.search(r'(\{[^{}]*"(?:entities|affected_entities)"[^{}]*\}|\[[^\[\]]*\])', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    if isinstance(data, dict):
                        if 'entities' in data:
                            companies = [str(e) for e in data['entities']]
                        elif 'affected_entities' in data:
                            companies = [str(e) for e in data['affected_entities']]
                    elif isinstance(data, list):
                        companies = [str(e) for e in data]
                    self.logger.debug(f"JSON parsed companies: {companies}")
                except json.JSONDecodeError as e:
                    self.logger.debug(f"JSON parse failed: {e}")
            
            # 2. JSON 파싱 실패 시 쉼표 기반 분리
            if not companies:
                clean_text = re.sub(r'[\"\'\[\]\{\}]', '', cleaned_text)
                companies = [c.strip() for c in clean_text.split(',') if c.strip()]
                self.logger.debug(f"Comma-split companies: {companies}")
            
            # 3. 유효성 검사 및 정제 (불용어 필터링)
            valid_companies = [
                c for c in companies 
                if not self._is_invalid_company_name(c)
            ][:3]
            
            self.logger.debug(f"Final valid companies: {valid_companies}")
            
            # 4. 결과 반환 (keyword 폴백 없음)
            return valid_companies
            
        except Exception as e:
            self.logger.error(f"LLM extraction error: {str(e)}")
            # 예외 시에도 빈 리스트 반환 (keyword 폴백 제거)
            return []
