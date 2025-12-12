"""
품질 검사 에이전트
온톨로지/그래프의 모순, 중복, 누락된 링크를 탐지
"""
from typing import List, Dict, Any, Optional
from ..utils.neo4j_client import Neo4jClient


class QualityCheckAgent:
    """
    지식 그래프의 품질을 검사하는 에이전트
    """
    
    def __init__(self, neo4j_client: Neo4jClient):
        """
        QualityCheckAgent 초기화
        
        Args:
            neo4j_client: Neo4j 클라이언트
        """
        self.neo4j_client = neo4j_client
    
    def check(self, graph_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        그래프 품질 검사
        
        Args:
            graph_data: 검사할 그래프 데이터 (선택, None이면 전체 그래프 검사)
        
        Returns:
            검사 결과 (이슈 목록, 이슈 존재 여부 등)
        """
        issues = []
        
        # 1. 스키마 일관성 검사
        schema_issues = self._check_schema_consistency()
        issues.extend(schema_issues)
        
        # 2. 엔티티 중복 검사
        duplicate_issues = self._check_duplicates()
        issues.extend(duplicate_issues)
        
        # 3. 관계 완전성 검사
        completeness_issues = self._check_completeness()
        issues.extend(completeness_issues)
        
        return {
            'issues': issues,
            'has_issues': len(issues) > 0,
            'schema_issues': [i for i in issues if 'schema' in i.get('type', '').lower()],
            'duplicate_issues': [i for i in issues if 'duplicate' in i.get('type', '').lower()],
            'completeness_issues': [i for i in issues if 'completeness' in i.get('type', '').lower()]
        }
    
    def _check_schema_consistency(self) -> List[Dict[str, Any]]:
        """
        스키마 일관성 검사
        
        Returns:
            발견된 스키마 이슈 목록
        """
        issues = []
        
        try:
            # Neo4j에서 스키마 정보 조회
            try:
                schema_result = self.neo4j_client.query("""
                    CALL db.schema.visualization()
                    YIELD nodes, relationships
                    RETURN nodes, relationships
                """)
            except Exception:
                # 스키마 조회 실패 시 기본 검사만 수행
                schema_result = None
            
            # 스키마 이슈 감지 로직
            # 예: 필수 노드 타입이 없는 경우
            required_node_types = ['Company', 'ProductLine', 'Metric']
            existing_node_types = []
            
            if schema_result:
                # 스키마 결과에서 노드 타입 추출
                # db.schema.visualization()은 노드와 관계 정보를 반환
                # 실제 구현 시 schema_result를 파싱하여 노드 타입 추출 필요
                # 현재는 간단한 검사만 수행
                for record in schema_result:
                    if hasattr(record, 'get'):
                        nodes = record.get('nodes', [])
                        if nodes:
                            # 노드 타입 추출 로직 (실제 구현 필요)
                            pass
            else:
                # 스키마 조회 실패 시 필수 노드 타입 존재 여부를 직접 확인
                for node_type in required_node_types:
                    try:
                        check_result = self.neo4j_client.query(f"""
                            MATCH (n:{node_type})
                            RETURN count(n) as count
                            LIMIT 1
                        """)
                        if not check_result or (check_result and len(check_result) == 0):
                            existing_node_types.append(node_type)  # 노드 타입은 존재하지만 데이터가 없을 수 있음
                    except Exception:
                        # 노드 타입이 존재하지 않을 수 있음
                        pass
            
            # 필수 노드 타입 누락 검사 (간단한 버전)
            # 실제로는 스키마 정보를 정확히 파싱해야 함
            # 현재는 스키마 조회가 실패한 경우에만 이슈로 표시
            if not schema_result:
                issues.append({
                    'type': 'schema_check_error',
                    'severity': 'medium',
                    'message': '스키마 정보를 조회할 수 없습니다. 스키마가 제대로 설정되었는지 확인하세요.'
                })
            
        except Exception as e:
            issues.append({
                'type': 'schema_check_error',
                'severity': 'high',
                'message': f'스키마 검사 중 오류 발생: {str(e)}'
            })
        
        return issues
    
    def _check_duplicates(self) -> List[Dict[str, Any]]:
        """
        엔티티 중복 검사
        
        Returns:
            발견된 중복 이슈 목록
        """
        issues = []
        
        try:
            # Company 노드 중복 검사
            duplicate_companies = self.neo4j_client.query("""
                MATCH (c:Company)
                WITH c.name AS name, collect(c) AS nodes
                WHERE size(nodes) > 1
                RETURN name, size(nodes) AS count
            """)
            
            if duplicate_companies:
                for record in duplicate_companies:
                    issues.append({
                        'type': 'duplicate_entity',
                        'severity': 'medium',
                        'message': f'중복된 Company 엔티티 발견: {record.get("name")} ({record.get("count")}개)',
                        'entity_type': 'Company',
                        'entity_name': record.get("name")
                    })
            
        except Exception as e:
            issues.append({
                'type': 'duplicate_check_error',
                'severity': 'medium',
                'message': f'중복 검사 중 오류 발생: {str(e)}'
            })
        
        return issues
    
    def _check_completeness(self) -> List[Dict[str, Any]]:
        """
        관계 완전성 검사
        
        Returns:
            발견된 완전성 이슈 목록
        """
        issues = []
        
        try:
            # Company 노드 중 관계가 없는 노드 검사
            isolated_companies = self.neo4j_client.query("""
                MATCH (c:Company)
                WHERE NOT (c)--()
                RETURN c.name AS name
                LIMIT 10
            """)
            
            if isolated_companies:
                for record in isolated_companies:
                    issues.append({
                        'type': 'completeness_isolated',
                        'severity': 'low',
                        'message': f'관계가 없는 Company 엔티티: {record.get("name")}',
                        'entity_type': 'Company',
                        'entity_name': record.get("name")
                    })
            
            # ProductLine 노드 중 Company와 연결되지 않은 노드 검사
            unlinked_products = self.neo4j_client.query("""
                MATCH (p:ProductLine)
                WHERE NOT (p)<-[:MANUFACTURES]-()
                RETURN p.name AS name
                LIMIT 10
            """)
            
            if unlinked_products:
                for record in unlinked_products:
                    issues.append({
                        'type': 'completeness_unlinked',
                        'severity': 'medium',
                        'message': f'Company와 연결되지 않은 ProductLine: {record.get("name")}',
                        'entity_type': 'ProductLine',
                        'entity_name': record.get("name")
                    })
            
        except Exception as e:
            issues.append({
                'type': 'completeness_check_error',
                'severity': 'medium',
                'message': f'완전성 검사 중 오류 발생: {str(e)}'
            })
        
        return issues
