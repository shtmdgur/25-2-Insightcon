from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.config.prompt_loader import PROMPTS
from src.models.nodes import RELATION_PROPERTIES_BY_TYPE

# LLM Tool Calling 지원 (Price + Graph)
ALL_TOOLS = []
try:
    from src.tools.price_tools import PRICE_TOOLS
    ALL_TOOLS.extend(PRICE_TOOLS)
except ImportError:
    pass

try:
    from src.tools.graph_tools import GRAPH_TOOLS
    ALL_TOOLS.extend(GRAPH_TOOLS)
except ImportError:
    pass

TOOLS_AVAILABLE = len(ALL_TOOLS) > 0

# 토론 라운드별 검색 전략 (Broad Search → LLM Cognitive Filtering)
# hop: 탐색 깊이, limit: 반환 경로 수
DEBATE_ROUND_STRATEGY = {
    1: {"hops": 2, "limit": 30},  # 1라운드: 얕고 넓게 - 다양한 논점
    2: {"hops": 3, "limit": 25},  # 2라운드: 중간 깊이
    3: {"hops": 4, "limit": 20}   # 3라운드: 깊이 탐색 - 핵심 인과
}

# 초기 노드 추출 시 타입당 최대 개수 (부족하면 LLM이 explore_graph Tool 호출)
NODE_EXTRACT_LIMIT = 10

class BaseDebateAgent(ABC):
    """
    변증법 토론 에이전트 베이스 클래스 (Cognitive Filtering 적용)
    
    설계 철학:
    - Rule-based Filtering 지양 (단순 키워드 매칭 X)
    - Broad Search & Cognitive Filtering 지향:
      1. 범용 경로 탐색 (Broad Search) -> 모든 가능성 열어둠
      2. 인지적 필터링 (Cognitive Filtering) -> LLM이 맥락에 맞춰 선별
    - Agentic Tool Calling: LLM이 필요 시 주가/그래프 데이터 동적 조회
    """
    
    def __init__(self, llm, neo4j_connection=None, role: str = "base"):
        self.llm = llm
        self.neo4j = neo4j_connection  # [Hybrid Access] 직접 Cypher 쿼리용
        self.role = role
        # 로드된 프롬프트 캐싱
        self.prompts = PROMPTS
        
        # Tool Binding (LLM이 주가/그래프 데이터 동적 조회 가능)
        if TOOLS_AVAILABLE and hasattr(llm, 'bind_tools'):
            self.llm_with_tools = llm.bind_tools(ALL_TOOLS)
        else:
            self.llm_with_tools = llm  # Fallback: 도구 없이 사용
    
    @abstractmethod
    def argue(
        self, 
        state: Dict[str, Any], 
        opponent_last_arg: Optional[str] = None
    ) -> Dict[str, str]:
        """
        주장 생성 (Cognitive Filtering 방식)
        
        절차:
        1. 문맥 및 로직 데이터 접근:
           - GraphRAG 서브그래프 (State에서 추출)
           - 직접 Cypher 쿼리 -> `_find_impact_paths` (범용 인과 경로)
        
        2. 인지적 필터링 (LLM):
           - 수집된 다양한 경로 중 자신의 관점(Role)에 부합하는 경로 식별.
           - 예: Bull은 "투자->성장" 경로 선택, Bear는 "투자->비용" 경로 선택.
        
        3. 논거 생성:
           - 선택된 경로를 근거(Provenance)로 제시하며 논리 구성.
        """
        pass
    
    def _extract_data_from_state(self, state: Dict) -> Dict:
        """
        State에서 데이터 추출 (Hybrid Access)
        1. GraphRAG 결과 파싱
        2. 범용 영향 경로(Impact Paths) 탐색 결과 병합 (Progressive Expansion)
        """
        target_companies = state.get("target_companies", [])
        target_company = target_companies[0] if target_companies else None

        
        # 토론 라운드 및 캐시 추출 (Progressive Path Expansion)
        debate_state = state.get("debate_state", {})
        debate_count = debate_state.get("debate_count", 1)
        cached_paths = debate_state.get("cached_paths", {})
        
        # Impact Paths 조회 (캐시 활용, 날짜 필터링 추가)
        impact_paths = []
        target_date = state.get("target_date")
        if target_company:
            impact_paths = self._find_impact_paths(target_company, debate_count, cached_paths, target_date)
        
        # 초기 Price 컨텍스트 조회 (target_date가 있는 경우)
        market_context = state.get("market_context", "")
        if not market_context:
            ticker = target_company if target_company else state.get("query", "")
            if target_date and ticker:
                try:
                    from src.utils.price_data_loader import PriceDataLoader
                    loader = PriceDataLoader()
                    market_context = loader.get_context(ticker, target_date)
                except Exception as e:
                    market_context = f"[Price 조회 실패: {e}]"
        
        # correlation 정보 추출 (impact_paths에서)
        correlation_summary = self._extract_correlation_summary(impact_paths)
        
        return {
            "agents": self._extract_nodes_by_type(state, ["IDM", "Fabless", "Foundry", "OSAT"]),
            "suppliers": self._extract_nodes_by_type(state, ["Supplier"]),
            "earnings": self._extract_nodes_by_type(state, ["Earnings"]),
            "price_moves": self._extract_nodes_by_type(state, ["PriceMovement"]),
            "issues": self._extract_nodes_by_type(state, ["Issue", "Disclosure"]),
            "macros": self._extract_nodes_by_type(state, ["EconomicIndicator"]),
            "impact_paths": impact_paths,
            "query": state.get("query", ""),
            "market_context": market_context,  # Price DB 시장 데이터
            "correlation": correlation_summary,  # 상관관계 요약 정보
            "document_summary": state.get("document_summary")  # [NEW] 문서 요약 정보
        }

    def _find_impact_paths(self, target_company: str, debate_count: int = 1, cached_paths: Dict[int, List[Dict]] = None, target_date: str = None) -> List[Dict]:
        """
        [Layered Traversal Strategy - Schema v3.0]
        
        레이어별 관계 탐색 (날짜 필터링 포함):
        1. Agent → Signal (HAS_SIGNAL): 기업 직접 시그널
        2. Signal → Signal (TRIGGERED_BY): 인과 체인
        3. Macro → Agent (AFFECTS): 거시경제 영향
        4. Agent ↔ Agent (COMPETES_WITH, PARTNERS_WITH, SUPPLIES): 경쟁/협력/공급망
        
        날짜 필터링 로직:
        - Signal 노드(Earnings, Issue 등)는 date 속성이 target_date보다 작거나 같은 경우만 포함
        """
        if not self.neo4j:
            return []
        
        # [NEW] 벡터 검색 기반 노드 선별 (Placeholder)
        # relevant_nodes = self._vector_search(target_company, limit=10)
        
        config = DEBATE_ROUND_STRATEGY.get(debate_count, DEBATE_ROUND_STRATEGY[1])
        total_limit = config["limit"]
        max_hops = config.get("hops", 2)  # 기본 2홉
        
        if cached_paths is None:
            cached_paths = {}
        
        # 이전 라운드 경로 수집
        accumulated_paths = []
        for round_num in range(1, debate_count):
            if round_num in cached_paths:
                accumulated_paths.extend(cached_paths[round_num])
        
        new_paths = []
        
        # ===== Broad Search: 모든 관계 탐색 (날짜 필터링 추가) =====
        # Signal 성격의 노드들은 기준일(target_date) 이전 데이터만 가져옴
        date_filter = ""
        if target_date:
            # 경로 내의 모든 노드 중 date가 있는 노드는 target_date 이하인 경우만 검사
            date_filter = "AND ALL(node in nodes(path) WHERE node.date IS NULL OR node.date <= $target_date)"

        broad_query = f"""
            MATCH path = (n)-[r*1..{max_hops}]-(target)
            WHERE target.name = $name {date_filter}
            RETURN path
            LIMIT {total_limit}
        """
        
        try:
            with self.neo4j.driver.session() as session:
                params = {"name": target_company}
                if target_date:
                    params["target_date"] = target_date
                result = session.run(broad_query, params)
                for record in result:
                    path_data = self._process_path_record(record)
                    if path_data:
                        new_paths.append(path_data)
        except Exception as e:
            print(f"[경고] Neo4j 쿼리 실패: {e}")
        
        all_paths = accumulated_paths + new_paths
        return all_paths[-total_limit:] if len(all_paths) > total_limit else all_paths

    def _vector_search(self, query: str, limit: int = 10) -> List[str]:
        """
        [Vector Search Implementation]
        Neo4j Vector Index를 활용하여 쿼리와 유사한 노드 검색
        
        Args:
            query: 검색 쿼리 (기업명 또는 이슈)
            limit: 반환할 최대 노드 수
        
        Returns:
            유사한 노드 이름 리스트
        """
        if not self.neo4j:
            return []
        
        try:
            # 1. 쿼리 임베딩 생성 (Gemini embedding)
            from google import genai
            import os
            
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=query
            )
            query_embedding = result.embeddings[0].values
            
            # 2. Neo4j Vector Index 쿼리
            with self.neo4j.driver.session() as session:
                # Vector Index가 존재하는 경우에만 쿼리 (없으면 fallback)
                vector_query = """
                    CALL db.index.vector.queryNodes('entity_embedding_index', $limit, $embedding)
                    YIELD node, score
                    RETURN node.name as name, score
                    ORDER BY score DESC
                """
                try:
                    result = session.run(vector_query, {
                        "embedding": query_embedding,
                        "limit": limit
                    })
                    return [record["name"] for record in result if record["name"]]
                except Exception as e:
                    # Vector Index가 없는 경우 이름 기반 검색으로 fallback
                    if "index" in str(e).lower() or "procedure" in str(e).lower():
                        print(f"[INFO] Vector Index 미구성, 이름 기반 검색으로 fallback")
                        fallback_query = """
                            MATCH (n)
                            WHERE n.name CONTAINS $query
                            RETURN n.name as name
                            LIMIT $limit
                        """
                        result = session.run(fallback_query, {"query": query, "limit": limit})
                        return [record["name"] for record in result if record["name"]]
                    raise
        except ImportError:
            print("[경고] google-genai 패키지 없음, 벡터 검색 스킵")
            return []
        except Exception as e:
            print(f"[경고] Vector Search 실패: {e}")
            return []
    
    def _process_path_record(self, record) -> Optional[Dict]:
        """Neo4j Path 레코드를 딕셔너리로 변환 (공통 로직)"""
        try:
            p = record["path"]
            
            # 노드 추출 (모든 속성 포함)
            nodes = []
            for n in p.nodes:
                try:
                    if hasattr(n, 'items'):
                        node_dict = {k: v for k, v in n.items()}
                        # 라벨 추출 (노드 타입)
                        if hasattr(n, 'labels'):
                            node_dict["_labels"] = list(n.labels)
                        nodes.append(node_dict)
                    elif hasattr(n, '__dict__'):
                        nodes.append(dict(n))
                    else:
                        nodes.append({"name": str(n)})
                except Exception:
                    nodes.append({"name": str(n)})
            
            # 관계 추출 (타입 + 속성)
            rels = []
            for r in p.relationships:
                try:
                    r_data = {"type": "UNKNOWN", "properties": {}}
                    if hasattr(r, 'type'):
                        r_data["type"] = r.type
                    else:
                        r_data["type"] = str(r)
                    
                    if hasattr(r, 'items'):
                        r_data["properties"] = {k: v for k, v in r.items()}
                    elif hasattr(r, '_properties'):
                        r_data["properties"] = dict(r._properties)
                    
                    rels.append(r_data)
                except Exception as e:
                    print(f"Rel extraction error: {e}")
                    rels.append({"type": "UNKNOWN", "properties": {}})
            
            # 텍스트 표현 생성
            chain_text = self._build_chain_text(nodes, rels)
            
            return {
                "text": chain_text,
                "nodes": nodes,
                "relationships": rels,
                "hop_depth": len(rels)
            }
        except Exception as e:
            print(f"[경고] Path 처리 실패: {e}")
            return None
    
    def _extract_correlation_summary(self, impact_paths: List[Dict]) -> str:
        """
        Impact Paths에서 correlation 정보 추출 및 요약
        
        Args:
            impact_paths: _find_impact_paths()에서 반환된 경로 목록
            
        Returns:
            상관관계 요약 문자열 (예: "DIRECT: 5건, INVERSE: 2건")
        """
        if not impact_paths:
            return "상관관계 데이터 없음"
        
        correlation_counts = {"DIRECT": 0, "INVERSE": 0, "null": 0}
        correlation_details = []
        
        for path in impact_paths:
            rels = path.get("relationships", [])
            for rel in rels:
                props = rel.get("properties", {})
                corr = props.get("correlation")
                
                if corr == "DIRECT":
                    correlation_counts["DIRECT"] += 1
                    # 세부 정보 추출
                    rel_type = rel.get("type", "UNKNOWN")
                    correlation_details.append(f"{rel_type}(DIRECT)")
                elif corr == "INVERSE":
                    correlation_counts["INVERSE"] += 1
                    rel_type = rel.get("type", "UNKNOWN")
                    correlation_details.append(f"{rel_type}(INVERSE)")
                else:
                    correlation_counts["null"] += 1
        
        # 요약 문자열 생성
        summary_parts = []
        if correlation_counts["DIRECT"] > 0:
            summary_parts.append(f"DIRECT(정방향): {correlation_counts['DIRECT']}건")
        if correlation_counts["INVERSE"] > 0:
            summary_parts.append(f"INVERSE(역방향): {correlation_counts['INVERSE']}건")
        
        if not summary_parts:
            return "상관관계 정보 미포함"
        
        summary = ", ".join(summary_parts)
        
        # 상위 5개 세부 정보 추가
        if correlation_details:
            top_details = correlation_details[:5]
            summary += f" | 예시: {', '.join(top_details)}"
        
        return summary

    
    def _build_chain_text(self, nodes: List[Dict], rels: List[Dict]) -> str:
        """노드-관계 체인을 텍스트로 변환 (LLM 가독성)"""
        chain_text = ""
        for i in range(len(rels)):
            node_name = nodes[i].get("name", "Unknown") if isinstance(nodes[i], dict) else str(nodes[i])
            node_type = ""
            if isinstance(nodes[i], dict) and "_labels" in nodes[i]:
                node_type = f":{nodes[i]['_labels'][0]}" if nodes[i]['_labels'] else ""
            
            rel_type = rels[i].get("type", "UNKNOWN")
            rel_props = rels[i].get("properties", {})
            
            # 스키마 기반 동적 속성 추출
            type_props = RELATION_PROPERTIES_BY_TYPE.get(rel_type, [])
            valid_props = []
            for k in type_props:
                if k in rel_props and rel_props[k] is not None:
                    valid_props.append(f"{k}:{rel_props[k]}")
            
            props_str = f" {{{', '.join(valid_props)}}}" if valid_props else ""
            chain_text += f"({node_name}{node_type}) --[{rel_type}{props_str}]--> "
        
        if nodes:
            last_node = nodes[-1]
            last_name = last_node.get("name", "Unknown") if isinstance(last_node, dict) else str(last_node)
            last_type = ""
            if isinstance(last_node, dict) and "_labels" in last_node:
                last_type = f":{last_node['_labels'][0]}" if last_node['_labels'] else ""
            chain_text += f"({last_name}{last_type})"
        
        return chain_text

    def _extract_nodes_by_type(self, state: Dict, types: List[str]) -> List[Dict]:
        """
        특정 타입의 노드 추출 (Neo4j 직접 쿼리)
        
        graphrag_results가 비어있으므로 Neo4j에서 직접 조회
        """
        if not self.neo4j:
            return []
        
        nodes = []
        target_company = state.get("target_companies", [None])[0]
        
        try:
            target_date = state.get("target_date")
            with self.neo4j.driver.session() as session:
                # 타겟 기업과 연결된 특정 타입 노드 조회
                for node_type in types:
                    date_filter = ""
                    if target_date:
                        date_filter = "AND (n.date IS NULL OR n.date <= $target_date)"

                    query = f"""
                        MATCH (n:{node_type})
                        WHERE n.name IS NOT NULL {date_filter}
                        OPTIONAL MATCH (n)-[r]-(target)
                        WHERE target.name = $target
                        RETURN DISTINCT n
                        LIMIT {NODE_EXTRACT_LIMIT}
                    """
                    params = {"target": target_company or ""}
                    if target_date:
                        params["target_date"] = target_date
                    result = session.run(query, params)
                    for record in result:
                        n = record["n"]
                        if hasattr(n, 'items'):
                            node_dict = {k: v for k, v in n.items()}
                        elif hasattr(n, '__dict__'):
                            node_dict = dict(n)
                        else:
                            node_dict = {"name": str(n)}
                        node_dict["type"] = node_type
                        nodes.append(node_dict)
        except Exception as e:
            print(f"[경고] 노드 추출 실패: {e}")
        
        return nodes

    def _build_prompt(self, query: str, data: Dict, opponent_arg: Optional[str], history: str) -> str:
        """
        프롬프트 생성 (YAML 템플릿 활용)
        """
        # 1. 템플릿 로드
        agent_key = self.role.lower()
        if agent_key == "base": 
            # 하위 클래스에서 role을 올바르게 설정해야 함
            return ""
            
        template = self.prompts.get("debate_agents", {}).get(agent_key, {}).get("instruction", "")
        
        # 2. 데이터 컨텍스트 포맷팅
        data_context = self._format_data_context(data)
        
        # 3. 템플릿 채우기 (안전한 문자열 대체 - format() 대신 replace() 사용)
        # format()은 데이터에 중괄호가 있으면 오류 발생 가능
        prompt = template
        prompt = prompt.replace("{ticker}", str(query))
        prompt = prompt.replace("{data_context}", str(data_context))
        prompt = prompt.replace("{bull_history}", str(history))
        prompt = prompt.replace("{bear_history}", str(history))
        prompt = prompt.replace("{critical_paths}", str(data.get("impact_paths", [])))
        prompt = prompt.replace("{correlation}", str(data.get("correlation", "상관관계 데이터 없음")))
        prompt = prompt.replace("{market_context}", str(data.get("market_context", "시장 컨텍스트 없음")))
        prompt = prompt.replace("{round_num}", str(data.get("round_num", 1)))
        prompt = prompt.replace("{history}", str(history))

        # [옵션] 상대방 반박 추가 (Bull/Bear)
        if opponent_arg:
            rebuttal_template = self.prompts.get("debate_agents", {}).get("base", {}).get("opponent_rebuttal", "")
            if rebuttal_template:
                rebuttal = rebuttal_template.replace("{opponent_arg}", str(opponent_arg))
                prompt += "\n" + rebuttal
            
        return prompt

    def _format_data_context(self, data: Dict[str, Any]) -> str:
        """
        Data Dict를 프롬프트에 삽입할 텍스트로 변환 (기존 로직 + YAML Base Summary)
        """
        base_summary_tpl = self.prompts.get("debate_agents", {}).get("base", {}).get("data_summary", "")
        
        # 기본 요약 생성 (prompts.yaml의 base.data_summary 키와 정확히 일치시켜야 함)
        summary = base_summary_tpl.format(
            query=data.get("query", "알 수 없음"),
            agent_count=len(data.get("agents", [])),
            supplier_count=len(data.get("suppliers", [])),
            earnings_count=len(data.get("earnings", [])),
            price_move_count=len(data.get("price_moves", [])),
            issue_count=len(data.get("issues", [])),
            macro_count=len(data.get("macros", [])),
            path_count=len(data.get("impact_paths", [])),
            document_context=self._format_document_summary(data.get("document_summary"))
        )
        
        details = []
        
        # 상세 데이터 리스팅
        # 1. Signals (Earnings & Price & Issues)
        all_signals = data.get("earnings", []) + data.get("price_moves", []) + data.get("issues", [])
        if all_signals:
            details.append("\n### Signals (Events & Issues)")
            for s in all_signals[:8]: # 상위 8개만 표시
                name = s.get('name', 'Unknown')
                stype = s.get('type', 'Unknown')
                desc = s.get('properties', {}).get('description') or s.get('description', '')
                if not desc and 'magnitude' in s:
                    desc = f"{s.get('direction')} {s.get('magnitude')}"
                details.append(f"- [{stype}] {name}: {desc}")

        # 2. Macros
        macros = data.get("macros", [])
        if macros:
            details.append("\n### Macro Indices")
            for m in macros[:3]:
                details.append(f"- {m.get('name', 'Unknown')}")

        # 3. Impact Paths
        impact_paths = data.get("impact_paths", [])
        if impact_paths:
            details.append("\n### Impact Paths (인과 경로)")
            for i, p in enumerate(impact_paths[:10]):
                details.append(f"- [Path {i+1}] {p.get('text', 'N/A')}")
        
        # 4. Market Context (Price DB) - 시장 상황 데이터
        market_context = data.get("market_context", "")
        if market_context:
            details.append("\n### Market Context (시장 상황)")
            details.append(market_context)
                
        return summary + "\n".join(details)
    
    def _format_document_summary(self, doc_sum: Optional[Dict[str, Any]]) -> str:
        """
        문서 요약 정보를 텍스트로 변환
        """
        if not doc_sum or not isinstance(doc_sum, dict):
            return "제공된 추가 문서 컨텍스트 없음"
            
        topic = doc_sum.get("main_topic", "알 수 없음")
        points = doc_sum.get("key_points", [])
        
        formatted = f"- **주요 주제**: {topic}\n"
        if points:
            formatted += "- **핵심 내용**:\n"
            for p in points:
                formatted += f"  * {p}\n"
        
        return formatted
        
    def _parse_response(self, response: Any) -> Dict[str, str]:
        """LLM 응답 처리 (단순 텍스트 반환)"""
        if hasattr(response, "content"):
            content = response.content
            # Gemini API의 content가 리스트일 경우 (content_parts)
            if isinstance(content, list):
                # 각 파트에서 'text' 필드만 추출하여 결합
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and 'text' in part:
                        text_parts.append(part['text'])
                    elif isinstance(part, str):
                        text_parts.append(part)
                return {"argument": "\n".join(text_parts)}
            # content가 문자열인 경우
            return {"argument": content}
        return {"argument": str(response)}
