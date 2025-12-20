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
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        뉴스 CSV를 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: CSV 파일 경로 (Semiconductor_News_Raw_*.csv)
        
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
            self.logger.info(f"Par뉴스 CSV: {file_path}")
            
            # CSV 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 검증
            self._validate_columns(df)
            
            # Knowledge Graph 생성
            kg = self._create_knowledge_graph(df, file_path)
            
            self.logger.info(
                f"News CSV parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse news CSV {file_path}: {str(e)}")
            raise ValueError(f"News CSV parsing failed: {str(e)}")
    
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
        
        # Event 엔티티 확인
        has_events = any(
            e.get("type") == NodeType.EVENT.value
            for e in data["entities"]
        )
        
        if not has_events:
            self.logger.warning("No Event entities found")
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
        file_path: Path
    ) -> KnowledgeGraph:
        """
        DataFrame을 Knowledge Graph로 변환
        
        Args:
            df: 뉴스 DataFrame
            file_path: 원본 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = []
        relations = []
        
        # 컬럼명 소문자로 정규화
        df.columns = [col.lower() for col in df.columns]
        
        # 날짜 파싱
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()]  # 날짜 없는 행 제거
        df = df.sort_values('date', ascending=False)  # 최신순 정렬
        
        # 샘플링
        from src.config.parser_config import get_config
        config = get_config('news')
        
        sample_size = min(config.sample_size, len(df))
        sampled_df = df.head(sample_size)
        
        self.logger.info(f"Processing {sample_size} news items out of {len(df)}")
        
        for idx, row in sampled_df.iterrows():
            # Event 엔티티 생성 (동적 KG)
            date_str = row['date'].strftime('%Y-%m-%d')
            title = str(row.get('title', ''))[:config.max_title_length]
            
            event_entity = Entity(
                name=f"NewsEvent_{idx}_{date_str}",
                type=NodeType.EVENT,
                properties={
                    "date": date_str,
                    "event_type": "뉴스",
                    "title": title,
                    "description": str(row.get('description', ''))[:config.max_desc_length],
                    "keyword": str(row.get('keyword', '')),
                    "link": str(row.get('link', '')),
                    "time_decay_weight": self._calculate_time_decay(date_str)
                },
                confidence=0.8  # 뉴스는 약간 낮은 신뢰도
            )
            entities.append(event_entity)
            
            # LLM 기반 affected_entities 추출 및 관계 생성
            keyword = str(row.get('keyword', '')).strip()
            
            if self.event_extractor and self.llm:
                # LLM으로 affected_entities 추출
                try:
                    affected_entities = self._extract_affected_entities(
                        title=title,
                        description=str(row.get('description', '')),
                        keyword=keyword
                    )
                    
                    for company_name in affected_entities:
                        relation = Relation(
                            subject=company_name,
                            predicate=RelationType.AFFECTED_BY,
                            object=event_entity.name,
                            weight=event_entity.properties['time_decay_weight'],
                            source=str(file_path)
                        )
                        relations.append(relation)
                        
                except Exception as e:
                    self.logger.warning(f"LLM extraction failed: {str(e)}. Using keyword fallback.")
                    # Fallback: keyword 사용
                    if keyword:
                        relation = Relation(
                            subject=keyword,
                            predicate=RelationType.AFFECTED_BY,
                            object=event_entity.name,
                            weight=event_entity.properties['time_decay_weight'],
                            source=str(file_path)
                        )
                        relations.append(relation)
            else:
                # LLM 없이: keyword 기반 매핑
                if keyword:
                    relation = Relation(
                        subject=keyword,
                        predicate=RelationType.AFFECTED_BY,
                        object=event_entity.name,
                        weight=event_entity.properties['time_decay_weight'],
                        source=str(file_path)
                    )
                    relations.append(relation)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_file": str(file_path),
                "file_type": "news_csv",
                "total_news": len(df),
                "sampled_news": sample_size,
                "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}"
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
            # LLM 프롬프트
            prompt = f"""
다음 뉴스에서 영향을 받는 기업/회사 이름을 추출하세요.

제목: {title}
본문: {description[:500]}
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
            extracted_text = response.content.strip()
            
            # 쉼표로 분리 및 정규화
            companies = [
                c.strip()
                for c in extracted_text.split(',')
                if c.strip()
            ][:3]  # 최대 3개
            
            self.logger.debug(f"LLM extracted: {companies}")
            
            return companies if companies else [keyword]
            
        except Exception as e:
            self.logger.error(f"LLM extraction error: {str(e)}")
            return [keyword] if keyword else []
