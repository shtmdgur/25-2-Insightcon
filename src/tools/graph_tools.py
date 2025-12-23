"""
Graph Exploration Tools for LLM Tool Calling

LLM이 동적으로 호출할 수 있는 그래프 탐색 도구
"""
from langchain_core.tools import tool
from typing import Optional


@tool
def explore_graph(target: str, hops: int = 2, limit: int = 20, relation_filter: Optional[str] = None) -> str:
    """
    특정 엔티티를 중심으로 Knowledge Graph를 탐색합니다.
    
    Args:
        target: 탐색 중심 엔티티 이름 (예: "삼성전자", "NVIDIA")
        hops: 탐색 깊이 (1~5, 기본값 2). 높을수록 더 먼 관계 탐색
        limit: 반환할 경로 수 (1~50, 기본값 20)
        relation_filter: 특정 관계만 탐색 (선택). 
                         예: "SUPPLIES", "COMPETES_WITH", "AFFECTS"
    
    Returns:
        탐색된 경로들의 요약 (노드 타입, 관계 타입, 속성 포함)
    
    Examples:
        - explore_graph("삼성전자", hops=2, limit=10) → 2홉 내 10개 경로
        - explore_graph("NVIDIA", hops=3, relation_filter="SUPPLIES") → 공급망만 탐색
    """
    from src.utils.neo4j_client import Neo4jClient
    from src.models.nodes import RELATION_PROPERTIES_BY_TYPE
    
    # 파라미터 범위 제한
    hops = max(1, min(5, hops))
    limit = max(1, min(50, limit))
    
    try:
        neo4j = Neo4jClient()
        
        # 관계 필터가 있으면 특정 관계만, 없으면 모든 관계
        if relation_filter:
            rel_pattern = f"[r:{relation_filter}*1..{hops}]"
        else:
            rel_pattern = f"[r*1..{hops}]"
        
        query = f"""
            MATCH path = (n)-{rel_pattern}-(target)
            WHERE target.name = $name
            RETURN path
            LIMIT {limit}
        """
        
        with neo4j.driver.session() as session:
            result = session.run(query, {"name": target})
            paths = []
            
            for record in result:
                p = record["path"]
                path_parts = []
                
                for i, node in enumerate(p.nodes):
                    # 노드 정보 추출
                    labels = list(node.labels) if hasattr(node, 'labels') else []
                    name = node.get("name", "Unknown")
                    node_type = labels[0] if labels else "Unknown"
                    path_parts.append(f"({name}:{node_type})")
                    
                    # 관계 정보 추출 (마지막 노드 제외)
                    if i < len(p.relationships):
                        rel = p.relationships[i]
                        rel_type = rel.type if hasattr(rel, 'type') else "UNKNOWN"
                        
                        # 관계 속성 추출
                        prop_keys = RELATION_PROPERTIES_BY_TYPE.get(rel_type, [])
                        props = {k: rel.get(k) for k in prop_keys if rel.get(k) is not None}
                        prop_str = ", ".join([f"{k}:{v}" for k, v in props.items()])
                        
                        if prop_str:
                            path_parts.append(f"--[{rel_type} {{{prop_str}}}]-->")
                        else:
                            path_parts.append(f"--[{rel_type}]-->")
                
                paths.append(" ".join(path_parts))
        
        if not paths:
            return f"'{target}'와 연결된 경로를 찾을 수 없습니다 (hops={hops}, limit={limit})."
        
        result_text = f"[{target}] {hops}홉 탐색 결과 ({len(paths)}개 경로):\n"
        for i, path in enumerate(paths, 1):
            result_text += f"{i}. {path}\n"
        
        return result_text
        
    except Exception as e:
        return f"그래프 탐색 오류: {e}"


# Tool list for binding
GRAPH_TOOLS = [explore_graph]
