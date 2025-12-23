"""
KG Construction Agent - Multi-Agent Orchestrator

모든 Parser Agent를 통합 관리하여 data/raw에서 Neo4j까지 자동 파이프라인을 구축합니다.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from src.agents.parsers.base_parser_agent import BaseParserAgent
from src.agents.parsers.pdf_parser_agent import GeminiPDFParser
# from src.agents.parsers.price_parser_agent import PriceParserAgent  # v3.0: 사용 안 함
from src.agents.parsers.news_parser_agent import NewsParserAgent
from src.agents.parsers.macro_parser_agent import MacroParserAgent
from src.agents.parsers.fund_parser_agent import FundParserAgent
from src.agents.parsers.dart_parser_agent import DARTParserAgent  # v3.0: 추가

from src.models.nodes import KnowledgeGraph
from src.dataflows.kg_merger import KGMerger
from src.dataflows.entity_normalizer import get_entity_normalizer  # 기존 (fallback)
from src.utils.entity_matcher import get_entity_matcher  # YAML 기반 정규화
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
            llm: LLM 모델 (NewsParser용)
        """
        import os
        from dotenv import load_dotenv
        load_dotenv()

        self.data_dir = data_dir or Path("data")
        self.raw_dir = self.data_dir / "raw"                  # PDF 원본
        self.preprocessed_dir = self.data_dir / "preprocessed"  # CSV 입력 데이터
        self.processed_dir = self.data_dir / "processed"         # JSON 결과 출력
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Parser Agents 초기화 (v3.0 스키마 반영)
        self.pdf_parser = GeminiPDFParser(use_batch=False)
        # self.price_parser = PriceParserAgent()  # v3.0: 사용 안 함
        self.news_parser = NewsParserAgent(llm=llm) if llm else NewsParserAgent()
        self.macro_parser = MacroParserAgent()
        self.fund_parser = FundParserAgent()
        self.dart_parser = DARTParserAgent()  # v3.0: 추가
        
        # 유틸리티
        self.merger = KGMerger()
        self.entity_matcher = get_entity_matcher()  # YAML 기반 정규화
        
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
        load_to_neo4j: bool = False,
        skip_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Knowledge Graph 자동 구축
        
        Args:
            data_sources: 수동 소스 지정 (예: {'pdf': [Path(...)], 'price': [...]})
            auto_scan: data/raw 자동 스캔 여부 (기본 True)
            use_batch: Batch API 사용 여부 (뉴스 파서 전용)
            load_to_neo4j: Neo4j 직접 주입 여부
            skip_existing: 이미 결과 파일이 존재하면 파싱 건너뛰기 (기본 False)
        
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
            parser_results = self._orchestrate_parsers(data_sources, use_batch, skip_existing)
            
            # 3. JSON 수집
            json_files = self._collect_json_files()
            
            # 4. 병합 및 정제
            merged_kg = self._merge_and_refine(json_files)
            
            # 5. Entity 정규화
            normalized_kg = self._normalize_entities(merged_kg)
            
            # 5.5 병합된 JSON 저장 (디버깅용)
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            merged_output_path = self.processed_dir / f"merged_kg_{timestamp}.json"
            normalized_kg.save_to_json(str(merged_output_path))
            logger.info(f"Merged & Normalized KG saved to {merged_output_path}")

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
        data/preprocessed/* 자동 스캔 (CSV 입력 데이터)
        
        Returns:
            파일 타입별 경로 목록
        """
        logger.info(f"Scanning data sources in {self.preprocessed_dir}")
        
        sources = {
            'pdf': [],
            'dart': [],  # v3.0: 추가
            'news': [],
            'macro': [],
            'fund': []
            # 'price': []  # v3.0: 제거
        }
        
        if not self.preprocessed_dir.exists():
            logger.warning(f"Preprocessed data directory not found: {self.preprocessed_dir}")
            return sources
        
        # PDF 파일은 preprocessed/reports, preprocessed/ir에서 스캔
        for pdf_dir in ['reports', 'ir']:
            pdf_path = self.preprocessed_dir / pdf_dir
            if pdf_path.exists():
                sources['pdf'].extend(list(pdf_path.glob('**/*.pdf')))
        
        # DART 디렉토리 (preprocessed에서)
        dart_path = self.preprocessed_dir / 'dart'
        if dart_path.exists():
            sources['dart'] = [dart_path]  # 디렉토리 자체를 전달
        
        # 뉴스 CSV (preprocessed에서)
        news_path = self.preprocessed_dir / 'news'
        if news_path.exists():
            sources['news'] = list(news_path.glob('*.csv'))
        
        # 매크로 (preprocessed에서)
        macro_path = self.preprocessed_dir / 'macro'
        if macro_path.exists():
            sources['macro'] = list(macro_path.glob('*.csv'))
        
        # 펀더멘털 (preprocessed에서)
        fund_path = self.preprocessed_dir / 'fund'
        if fund_path.exists():
            sources['fund'] = list(fund_path.glob('*.csv'))
        
        # 통계 출력
        for source_type, files in sources.items():
            count = len(files) if isinstance(files, list) else 1
            logger.info(f"  - {source_type}: {count} files")
        
        return sources
    
    def _orchestrate_parsers(
        self,
        data_sources: Dict[str, List[Path]],
        use_batch: bool,
        skip_existing: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Parser Agent 실행
        
        Args:
            data_sources: 파일 타입별 경로 목록
            use_batch: Batch API 사용 여부
            skip_existing: 이미 결과 파일이 존재하면 파싱 건너뛰기
        
        Returns:
            파서별 실행 결과
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info("Orchestrating Parser Agents (병렬 처리)...")
        
        results = {}
        
        # 1. PDF (가장 무거우므로 먼저 실행하거나 별도 관리)
        if data_sources.get('pdf'):
            results['pdf'] = self._batch_parse_pdfs(data_sources['pdf'], skip_existing)
        
        # 병렬 처리할 파서 정의
        def run_dart():
            if not data_sources.get('dart'):
                return 'dart', None
            result = {'total': 0, 'success': 0, 'failed': 0}
            for dart_dir in data_sources['dart']:
                try:
                    # 건너뛰기 체크
                    output_file = self.processed_dir / "dart_kg.json"
                    if skip_existing and output_file.exists():
                        logger.info(f"Skipping existing DART KG: {output_file.name}")
                        result['success'] += 1
                        result['total'] += 1
                        continue

                    kg = self.dart_parser.parse(dart_dir)
                    kg.save_to_json(str(output_file))
                    result['success'] += 1
                    result['total'] += 1
                    logger.info(f"   ✓ DART: {len(kg.entities)} entities")
                except Exception as e:
                    result['failed'] += 1
                    result['total'] += 1
                    logger.error(f"   ✗ DART: {e}")
            return 'dart', result
        
        def run_news():
            if not data_sources.get('news') or not self.news_parser:
                return 'news', None
            return 'news', self.news_parser.batch_parse(
                data_sources['news'], 
                self.processed_dir,
                skip_existing=skip_existing
            )
        
        def run_macro():
            if not data_sources.get('macro'):
                return 'macro', None
            return 'macro', self.macro_parser.batch_parse(
                data_sources['macro'], 
                self.processed_dir,
                skip_existing=skip_existing
            )
        
        def run_fund():
            if not data_sources.get('fund'):
                return 'fund', None
            return 'fund', self.fund_parser.batch_parse(
                data_sources['fund'], 
                self.processed_dir,
                skip_existing=skip_existing
            )
        
        # 병렬 실행 (DART, News, Macro, Fund)
        logger.info("Running CSV Parsers (병렬 처리)...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(run_dart),
                executor.submit(run_news),
                executor.submit(run_macro),
                executor.submit(run_fund)
            ]
            for future in as_completed(futures):
                try:
                    parser_name, result = future.result()
                    if result:
                        results[parser_name] = result
                        logger.info(f"   ✓ {parser_name}: 완료")
                except Exception as e:
                    logger.error(f"   ✗ 파서 실행 오류: {e}")
        
        return results
    
    def _batch_parse_pdfs(
        self, 
        pdf_files: List[Path],
        skip_existing: bool = False
    ) -> Dict[str, Any]:
        """
        PDF 파일 배치 파싱
        
        Args:
            pdf_files: PDF 파일 경로 리스트
            skip_existing: 이미 결과 파일이 존재하면 파싱 건너뛰기
        
        Returns:
            파싱 결과 통계
        """
        total = len(pdf_files)
        success = 0
        failed = 0
        errors = []
        
        for pdf_file in pdf_files:
            try:
                # 파일 검증
                if not pdf_file.exists():
                    raise ValueError(f"File not found: {pdf_file}")
                if pdf_file.suffix.lower() != '.pdf':
                    raise ValueError(f"Not a PDF file: {pdf_file}")
                
                # 0. 건너뛰기 체크
                output_file = self.processed_dir / f"{pdf_file.stem}_kg.json"
                if skip_existing and output_file.exists():
                    logger.info(f"Skipping existing PDF KG: {pdf_file.name}")
                    success += 1
                    continue

                # PDFParserAgent로 파싱
                logger.info(f"Parsing PDF: {pdf_file}")
                result = self.pdf_parser.parse(str(pdf_file))  # parse_pdf_to_kg → parse 수정
                kg = result["knowledge_graph"]
                
                # 메타데이터 추가
                kg.metadata.update({
                    "source_file": str(pdf_file),
                    "file_type": "pdf"
                })
                
                # PDF parser가 이미 _kg.json을 저장하므로 여기서 추가 저장 불필요
                
                logger.info(
                    f"PDF parsed: {pdf_file.name} → "
                    f"{len(kg.entities)} entities, {len(kg.relations)} relations"
                )
                success += 1

                
            except Exception as e:
                logger.error(f"Failed to parse {pdf_file}: {str(e)}")
                errors.append(f"{pdf_file.name}: {str(e)}")
                failed += 1
        
        result = {
            'total': total,
            'success': success,
            'failed': failed
        }
        if errors:
            result['errors'] = errors
        
        return result
    
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
        Entity 정규화 (YAML 기반 마스터 리스트 + fuzzy matching)
        
        Args:
            kg: Knowledge Graph
        
        Returns:
            정규화된 KnowledgeGraph
        """
        logger.info("Normalizing entities with EntityMatcher...")
        
        # Entity 이름 정규화
        normalized_count = 0
        skipped_count = 0
        for entity in kg.entities:
            # 이미 정규화된 경우 스킵
            if entity.properties.get("_normalized"):
                skipped_count += 1
                continue
            
            # EntityMatcher 사용 (YAML 기반 + fuzzy matching)
            original_name = entity.name
            normalized_name = self.entity_matcher.match(entity.name)
            
            if normalized_name != original_name:
                logger.debug(f"Normalized: {original_name} → {normalized_name}")
                entity.name = normalized_name
                normalized_count += 1
            
            # 엔티티 정보 조회 (ticker 등)
            entity_info = self.entity_matcher.get_entity_info(normalized_name)
            if entity_info and entity_info.get('ticker'):
                entity.properties['ticker'] = entity_info['ticker']
            
            # 정규화 마커 추가
            entity.properties["_normalized"] = True
        
        logger.info(f"Normalized {normalized_count} entities (skipped {skipped_count} already normalized)")
        
        # Relation subject/object 정규화
        relation_normalized = 0
        for relation in kg.relations:
            # Subject
            original_subj = relation.subject
            relation.subject = self.entity_matcher.match(relation.subject)
            if relation.subject != original_subj:
                relation_normalized += 1
            
            # Object
            original_obj = relation.object
            relation.object = self.entity_matcher.match(relation.object)
            if relation.object != original_obj:
                relation_normalized += 1
        
        logger.info(f"Normalized {relation_normalized} relation endpoints")
        
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
        
        # 레이어별 통계 (v3.0: OSAT 추가)
        static_count = sum(
            1 for e in merged_kg.entities
            if e.type.value in ['IDM', 'Fabless', 'Foundry', 'OSAT', 'Supplier', 'Organization', 'EconomicIndicator']
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
