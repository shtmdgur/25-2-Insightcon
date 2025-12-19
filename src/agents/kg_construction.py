"""
KG Construction Agent - Multi-Agent Orchestrator

모든 Parser Agent를 통합 관리하여 data/raw에서 Neo4j까지 자동 파이프라인을 구축합니다.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from src.agents.parsers.base_parser_agent import BaseParserAgent
from src.agents.parsers.pdf_parser_agent import PDFParserAgent
from src.agents.parsers.price_parser_agent import PriceParserAgent
from src.agents.parsers.dart_parser_agent import DARTParserAgent
from src.agents.parsers.news_parser_agent import NewsParserAgent
from src.agents.parsers.macro_parser_agent import MacroParserAgent
from src.agents.parsers.fund_parser_agent import FundParserAgent

from src.models.nodes import KnowledgeGraph
from src.dataflows.kg_merger import KGMerger
from src.utils.entity_normalizer import get_entity_normalizer
from src.dataflows.neo4j_loader import Neo4jKGLoader

logger = logging.getLogger(__name__)


class KGConstructionAgent:
    """
    Knowledge Graph Construction Orchestrator
    
    역할:
    1. data/raw/* 자동 스캔
    2. Parser Agent 병렬 실행
    3. JSON 수집 및 병합
    4. Entity 정규화
    5. Neo4j 주입 (이중 레이어)
    6. 결과 리포트 생성
    """
    
    def __init__(
        self,
        data_dir: Path = None,
        neo4j_uri: str = None,
        llm=None
    ):
        """
        Args:
            data_dir: 데이터 루트 디렉토리 (기본: ./data)
            neo4j_uri: Neo4j 연결 URI
            llm: LLM 모델 (NewsParser용, PDFParser는 독립적으로 LLM 생성)
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()

        self.data_dir = data_dir or Path("data")
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Parser Agents 초기화
        self.pdf_parser = PDFParserAgent()  # 내부에서 독립적으로 LLM 생성
        self.price_parser = PriceParserAgent()
        self.dart_parser = DARTParserAgent()
        self.news_parser = NewsParserAgent(llm=llm) if llm else NewsParserAgent()  # LLM 전달
        self.macro_parser = MacroParserAgent()
        self.fund_parser = FundParserAgent()
        
        # 유틸리티
        self.merger = KGMerger()
        self.normalizer = get_entity_normalizer()
        
        if neo4j_uri:
            user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            self.loader = Neo4jKGLoader(uri=neo4j_uri, user=user, password=password)
        else:
            self.loader = None
        
        logger.info(f"KGConstructionAgent initialized (data_dir={self.data_dir}, llm={'provided' if llm else 'None'})")
    
    def construct_knowledge_graph(
        self,
        data_sources: Optional[Dict[str, List[Path]]] = None,
        auto_scan: bool = True,
        use_batch: bool = False,
        load_to_neo4j: bool = False
    ) -> Dict[str, Any]:
        """
        Knowledge Graph 자동 구축
        
        Args:
            data_sources: 수동 소스 지정 (예: {'pdf': [Path(...)], 'price': [...]})
            auto_scan: data/raw 자동 스캔 여부 (기본 True)
            use_batch: Batch API 사용 여부 (뉴스 파서 전용)
            load_to_neo4j: Neo4j 직접 주입 여부
        
        Returns:
            통계 리포트 {
                'parsers': {...},
                'json_files': int,
                'merged_entities': int,
                'merged_relations': int,
                'layers': {'static': int, 'dynamic': int}
            }
        """
        logger.info("=" * 80)
        logger.info("Knowledge Graph Construction Started")
        logger.info("=" * 80)
        
        try:
            # 1. 데이터 소스 스캔
            if auto_scan:
                data_sources = self._scan_data_sources()
            
            # 2. Parser Agent 실행
            parser_results = self._orchestrate_parsers(data_sources, use_batch)
            
            # 3. JSON 수집
            json_files = self._collect_json_files()
            
            # 4. 병합 및 정제
            merged_kg = self._merge_and_refine(json_files)
            
            # 5. Entity 정규화
            normalized_kg = self._normalize_entities(merged_kg)
            
            # 6. Neo4j 주입 (선택적)
            neo4j_stats = None
            if load_to_neo4j and self.loader:
                neo4j_stats = self._load_to_neo4j(normalized_kg)
            
            # 7. 결과 리포트
            report = self._generate_report(
                parser_results,
                json_files,
                normalized_kg,
                neo4j_stats
            )
            
            logger.info("=" * 80)
            logger.info("Knowledge Graph Construction Completed")
            logger.info("=" * 80)
            
            return report
            
        except Exception as e:
            logger.error(f"KG Construction failed: {str(e)}")
            raise
    
    def _scan_data_sources(self) -> Dict[str, List[Path]]:
        """
        data/raw/* 자동 스캔
        
        Returns:
            파일 타입별 경로 목록
        """
        logger.info(f"Scanning data sources in {self.raw_dir}")
        
        sources = {
            'pdf': [],
            'price': [],
            'dart': [],
            'news': [],
            'macro': [],
            'fund': []
        }
        
        if not self.raw_dir.exists():
            logger.warning(f"Raw data directory not found: {self.raw_dir}")
            return sources
        
        # PDF 파일 스캔
        # - reports: 애널리스트 리포트 (flat 구조)
        # - ir: IR 자료 (회사별 하위 폴더 구조, 예: ir/005930/report.pdf)
        for pdf_dir in ['reports', 'ir']:
            pdf_path = self.raw_dir / pdf_dir
            if pdf_path.exists():
                # **/*.pdf: 모든 하위 폴더 재귀 검색
                sources['pdf'].extend(list(pdf_path.glob('**/*.pdf')))
        
        # 주가 CSV (모든 CSV 파일, 다양한 티커 형식 지원)
        price_path = self.raw_dir / 'price'
        if price_path.exists():
            sources['price'] = list(price_path.glob('*.csv'))
        
        # DART (디렉토리 전체)
        dart_path = self.raw_dir / 'DART'
        if dart_path.exists():
            sources['dart'] = [dart_path]  # 디렉토리 자체 전달
        
        # 뉴스
        news_path = self.raw_dir / 'news'
        if news_path.exists():
            sources['news'] = list(news_path.glob('*.csv'))
        
        # 매크로
        macro_path = self.raw_dir / 'macro'
        if macro_path.exists():
            sources['macro'] = list(macro_path.glob('*.csv'))
        
        # 펀더멘탈 (*_fundamentals.csv 패턴)
        fund_path = self.raw_dir / 'fund'
        if fund_path.exists():
            sources['fund'] = list(fund_path.glob('*_fundamentals.csv'))
        
        # 통계 출력
        for source_type, files in sources.items():
            logger.info(f"  - {source_type}: {len(files)} files")
        
        return sources
    
    def _orchestrate_parsers(
        self,
        data_sources: Dict[str, List[Path]],
        use_batch: bool
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parser Agent 실행
        
        Args:
            data_sources: 파일 타입별 경로 목록
            use_batch: Batch API 사용 여부
        
        Returns:
            파서별 실행 결과
        """
        logger.info("Orchestrating Parser Agents...")
        
        results = {}
        
        # PDF Parser
        if data_sources.get('pdf'):
            logger.info(f"Running PDFParserAgent ({len(data_sources['pdf'])} files)")
            results['pdf'] = self.pdf_parser.batch_parse(
                data_sources['pdf'],
                self.processed_dir
            )
        
        # Price Parser
        if data_sources.get('price'):
            logger.info(f"Running PriceParserAgent ({len(data_sources['price'])} files)")
            results['price'] = self.price_parser.batch_parse(
                data_sources['price'],
                self.processed_dir
            )
        
        # DART Parser
        if data_sources.get('dart'):
            logger.info("Running DARTParserAgent")
            try:
                dart_kg = self.dart_parser.parse(data_sources['dart'][0])
                output_file = self.processed_dir / "dart_kg.json"
                self.dart_parser.to_json(dart_kg, output_file)
                results['dart'] = {'total': 1, 'success': 1, 'failed': 0}
            except Exception as e:
                logger.error(f"DART parsing failed: {str(e)}")
                results['dart'] = {'total': 1, 'success': 0, 'failed': 1, 'errors': [str(e)]}
        
        # News Parser (LLM 필요)
        if data_sources.get('news') and self.news_parser:
            logger.info(f"Running NewsParserAgent ({len(data_sources['news'])} files)")
            results['news'] = self.news_parser.batch_parse(
                data_sources['news'],
                self.processed_dir
            )
        elif data_sources.get('news'):
            logger.warning("NewsParserAgent skipped (LLM not initialized)")
        
        # Macro Parser
        if data_sources.get('macro'):
            logger.info(f"Running MacroParserAgent ({len(data_sources['macro'])} files)")
            results['macro'] = self.macro_parser.batch_parse(
                data_sources['macro'],
                self.processed_dir
            )
        
        # Fund Parser
        if data_sources.get('fund'):
            logger.info(f"Running FundParserAgent ({len(data_sources['fund'])} files)")
            results['fund'] = self.fund_parser.batch_parse(
                data_sources['fund'],
                self.processed_dir
            )
        
        return results
    
    def _collect_json_files(self) -> List[Path]:
        """
        data/processed/*_kg.json 수집
        
        Parser Agent가 생성한 KG JSON 파일만 수집 (패턴: *_kg.json)
        
        Returns:
            JSON 파일 경로 목록
        """
        json_files = list(self.processed_dir.glob('*_kg.json'))
        logger.info(f"Collected {len(json_files)} KG JSON files from {self.processed_dir}")
        return json_files
    
    def _merge_and_refine(self, json_files: List[Path]) -> KnowledgeGraph:
        """
        여러 KG JSON 병합
        
        Args:
            json_files: JSON 파일 경로 목록
        
        Returns:
            병합된 KnowledgeGraph
        """
        logger.info("Merging Knowledge Graphs...")
        
        # JSON 파일 로드
        kgs = []
        for json_file in json_files:
            try:
                kg = KnowledgeGraph.load_from_json(str(json_file))
                kgs.append(kg)
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {str(e)}")
        
        # 병합
        if not kgs:
            logger.warning("No KGs to merge")
            return KnowledgeGraph(entities=[], relations=[])
        
        merged_kg = self.merger.merge_knowledge_graphs(kgs)
        
        logger.info(
            f"Merged KG: {len(merged_kg.entities)} entities, "
            f"{len(merged_kg.relations)} relations"
        )
        
        return merged_kg
    
    def _normalize_entities(self, kg: KnowledgeGraph) -> KnowledgeGraph:
        """
        Entity 정규화
        
        Args:
            kg: Knowledge Graph
        
        Returns:
            정규화된 KnowledgeGraph
        """
        logger.info("Normalizing entities...")
        
        # Entity 이름 정규화
        for entity in kg.entities:
            # normalize_entity returns Dict: {'canonical_name': ..., 'ticker': ..., ...}
            normalization_result = self.normalizer.normalize_entity(entity.name)
            normalized_name = normalization_result.get('canonical_name', entity.name)
            
            if normalized_name != entity.name:
                logger.debug(f"Normalized: {entity.name} -> {normalized_name}")
                entity.name = normalized_name
                # 정규화된 정보(ticker 등)를 속성에 추가
                if normalization_result.get('ticker'):
                    entity.properties['ticker'] = normalization_result['ticker']
        
        # Relation subject/object 정규화
        for relation in kg.relations:
            # Subject
            subj_norm = self.normalizer.normalize_entity(relation.subject)
            relation.subject = subj_norm.get('canonical_name', relation.subject)
            
            # Object
            obj_norm = self.normalizer.normalize_entity(relation.object)
            relation.object = obj_norm.get('canonical_name', relation.object)
        
        return kg
    
    def _load_to_neo4j(self, kg: KnowledgeGraph) -> Dict[str, int]:
        """
        Neo4j 주입 (이중 레이어)
        
        Args:
            kg: Knowledge Graph
        
        Returns:
            주입 통계
        """
        logger.info("Loading to Neo4j...")
        
        if not self.loader:
            logger.warning("Neo4jKGLoader not initialized")
            return {}
        
        stats = self.loader.load_knowledge_graph(kg)
        
        logger.info(
            f"Neo4j loaded: {stats.get('static_nodes', 0)} static nodes, "
            f"{stats.get('dynamic_nodes', 0)} dynamic nodes, "
            f"{stats.get('relationships_created', 0)} relations"
        )
        
        return stats
    
    def _generate_report(
        self,
        parser_results: Dict[str, Dict[str, Any]],
        json_files: List[Path],
        merged_kg: KnowledgeGraph,
        neo4j_stats: Optional[Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        결과 리포트 생성
        
        Args:
            parser_results: 파서별 실행 결과
            json_files: JSON 파일 목록
            merged_kg: 병합된 KG
            neo4j_stats: Neo4j 주입 통계
        
        Returns:
            종합 리포트
        """
        report = {
            'parser_results': parser_results,
            'json_files': [str(f) for f in json_files],  # 개수 대신 파일 목록 반환
            'json_files_count': len(json_files),
            'merged_kg_summary': {
                'entities': len(merged_kg.entities),
                'relations': len(merged_kg.relations)
            },
            'merged_kg': merged_kg,  # 객체 자체도 포함 (테스트 코드에서 필요)
            'neo4j_stats': neo4j_stats if neo4j_stats else None
        }
        
        # 레이어별 통계
        static_count = sum(
            1 for e in merged_kg.entities
            if e.type.value in ['Company', 'Product', 'Technology', 'Person']
        )
        dynamic_count = len(merged_kg.entities) - static_count
        
        report['layers'] = {
            'static': static_count,
            'dynamic': dynamic_count
        }
        
        # 로깅용으로는 JSON 포맷만 (객체 제외)
        log_report = report.copy()
        log_report.pop('merged_kg') 
        logger.info(f"Report: {json.dumps(log_report, indent=2, ensure_ascii=False)}")
        
        # 리포트 저장 (타임스탬프 포함)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_path = self.processed_dir / f"kg_construction_report_{timestamp}.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(log_report, f, indent=2, ensure_ascii=False)
            logger.info(f"Report saved to {report_path}")
        except Exception as e:
            logger.warning(f"Failed to save report: {str(e)}")
        
        return report
