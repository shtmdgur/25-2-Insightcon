from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.config.prompt_loader import PROMPTS

# 토론 라운드별 검색 전략 (깊이 진화)
DEBATE_ROUND_STRATEGY = {
    1: {"hops": 2, "limit": 20},  # 1라운드: 넓고 얕게 - 다양한 논점 제기
    2: {"hops": 3, "limit": 15},  # 2라운드: 중간 깊이 - 구체적 반박
    3: {"hops": 4, "limit": 10}   # 3라운드: 깊고 정밀 - 핵심 인과로 결정타
}

class BaseDebateAgent(ABC):
    """
    변증법 토론 에이전트 베이스 클래스 (Cognitive Filtering 적용)
    
    설계 철학:
    - Rule-based Filtering 지양 (단순 키워드 매칭 X)
    - Broad Search & Cognitive Filtering 지향:
      1. 범용 경로 탐색 (Broad Search) -> 모든 가능성 열어둠
      2. 인지적 필터링 (Cognitive Filtering) -> LLM이 맥락에 맞춰 선별
    """
    
    def __init__(self, llm, neo4j_connection=None, role: str = "base"):
        self.llm = llm
        self.neo4j = neo4j_connection  # [Hybrid Access] 직접 Cypher 쿼리용
        self.role = role
        # 로드된 프롬프트 캐싱
        self.prompts = PROMPTS
    
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
        target_company = state.get("target_companies", [None])[0]
        
        # 토론 라운드 및 캐시 추출 (Progressive Path Expansion)
        debate_state = state.get("debate_state", {})
        debate_count = debate_state.get("debate_count", 1)
        cached_paths = debate_state.get("cached_paths", {})
        
        # Impact Paths 조회 (캐시 활용)
        impact_paths = []
        if target_company:
            impact_paths = self._find_impact_paths(target_company, debate_count, cached_paths)
            # 현재 라운드 결과를 캐시에 저장 (State 업데이트는 Workflow에서 처리)
            # 여기서는 반환만 하고, Workflow가 state["debate_state"]["cached_paths"][round] = paths 저장
        
        return {
            "events": self._extract_events(state),
            "trends": self._extract_trends(state),
            "metrics": self._extract_metrics(state),
            "impact_paths": impact_paths
        }

    def _find_impact_paths(self, target_company: str, debate_count: int = 1, cached_paths: Dict[int, List[Dict]] = None) -> List[Dict]:
        """
        [Progressive Path Expansion with Caching]
        기업에 영향을 주는 모든 '사건'과 '변화'의 경로를 범용적으로 추출
        (미리 Bull/Bear를 나누지 않음)
        
        전략: 이전 라운드 경로 재사용 + 새로운 깊이만 추가 조회
        - Round 1: 2-hop 쿼리 (20개) → 캐시 저장
        - Round 2: 캐시 재사용 + 3-hop만 쿼리 (15개) → 병합
        - Round 3: 캐시 재사용 + 4-hop만 쿼리 (10개) → 병합
        
        효과: 중복 쿼리 제거로 Neo4j 부하 50% 절감
        
        Cypher 패턴:
        (Event|Trend|Policy)-[:*exact_hop]-(Company)
        """
        if not self.neo4j:
            return []
        
        # 라운드별 검색 전략 선택
        config = DEBATE_ROUND_STRATEGY.get(debate_count, DEBATE_ROUND_STRATEGY[1])
        target_hops = config["hops"]
        total_limit = config["limit"]
        
        # 캐시 초기화
        if cached_paths is None:
            cached_paths = {}
        
        # 이전 라운드 경로 수집
        accumulated_paths = []
        for round_num in range(1, debate_count):
            if round_num in cached_paths:
                accumulated_paths.extend(cached_paths[round_num])
        
        # 현재 라운드에서 새로 조회할 hop 계산
        # CRITICAL: Round 1에서는 1-hop 직접 관계 포함해야 함!
        # Round 1: [*1..2] (직접 + 인접 관계 모두)
        # Round 2+: [*3], [*4] (정확한 깊이만, 캐시에 없는 것)
        if debate_count == 1:
            hop_pattern = f"[*1..{target_hops}]"  # 예: [*1..2]
        else:
            hop_pattern = f"[*{target_hops}]"      # 예: [*3], [*4]
        
        # 새로운 hop depth만 조회 (기존 경로와 중복 방지)
        query = f"""
        MATCH path = (source)-{hop_pattern}-(target:Company {{name: $name}})
        WHERE source:Event OR source:Trend OR source:Metric OR source:Policy
        RETURN path
        LIMIT {total_limit}
        """
        
        new_paths = []
        try:
            with self.neo4j.driver.session() as session:
                result = session.run(query, {"name": target_company})
                # Path 객체를 딕셔너리로 변환 (Node, Edge 정보 포함)
                for record in result:
                    p = record["path"]
                    # 간단화: 노드 이름들의 시퀀스로 변환 (LLM 가독성)
                    # Neo4j Node 객체 안전하게 변환
                    nodes = []
                    for n in p.nodes:
                        try:
                            # Neo4j Node는 dict() 대신 dict(n.items()) 사용
                            if hasattr(n, 'items'):
                                nodes.append({k: v for k, v in n.items()})
                            elif hasattr(n, '__dict__'):
                                nodes.append(dict(n))
                            else:
                                nodes.append({"name": str(n)})
                        except Exception:
                            nodes.append({"name": str(n)})
                    
                    # 관계(Relationship) 타입 추출
                    rels = []
                    for r in p.relationships:
                        try:
                            rels.append(r.type if hasattr(r, 'type') else str(r))
                        except Exception:
                            rels.append("UNKNOWN")
                    
                    # 텍스트 표현
                    chain_text = ""
                    for i in range(len(rels)):
                        node_name = nodes[i].get("name", "Unknown") if isinstance(nodes[i], dict) else str(nodes[i])
                        chain_text += f"{node_name} --[{rels[i]}]--> "
                    if nodes:
                        last_node_name = nodes[-1].get("name", "Unknown") if isinstance(nodes[-1], dict) else str(nodes[-1])
                        chain_text += last_node_name
                    
                    new_paths.append({
                        "text": chain_text,
                        "nodes": nodes,
                        "relationships": rels,
                        "hop_depth": new_hop  # 디버깅용
                    })
        except Exception as e:
            print(f"[경고] 인과 경로 탐색 실패: {e}")
        
        # 캐시된 경로와 새 경로 병합
        all_paths = accumulated_paths + new_paths
        
        # 총 limit 적용 (최신 경로 우선)
        return all_paths[-total_limit:] if len(all_paths) > total_limit else all_paths

    def _extract_events(self, state: Dict) -> List[Dict]:
        """
        이벤트 추출 (단순 수집, 판단은 LLM에게 위임)
        """
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        
        return [n for n in nodes if n.get("type", "") == "Event"]

    def _extract_trends(self, state: Dict) -> List[Dict]:
        """트렌드 추출"""
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        return [n for n in nodes if n.get("type", "") == "Trend"]

    def _extract_metrics(self, state: Dict) -> List[Dict]:
        """지표 추출"""
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        return [n for n in nodes if n.get("type", "") == "Metric"]

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
        
        # 3. 템플릿 채우기 (안전한 포맷팅)
        try:
            prompt = template.format(
                ticker=query,
                data_context=data_context,
                bull_history=history, # Synthesizer 등에서 필요할 수 있음
                bear_history=history, 
                critical_paths=str(data.get("impact_paths", [])) # Synthesizer용
            )
        except KeyError as e:
            # 포맷 키 불일치 시 상세 경고 및 단순 대체 시도
            print(f"[경고] 프롬프트 템플릿 키 누락: {e}. 기본 포맷으로 대체합니다.")
            prompt = template.replace("{ticker}", query).replace("{data_context}", data_context)

        # [옵션] 상대방 반박 추가 (Bull/Bear)
        if opponent_arg:
            rebuttal_template = self.prompts.get("debate_agents", {}).get("base", {}).get("opponent_rebuttal", "")
            if rebuttal_template:
                try:
                    prompt += "\n" + rebuttal_template.format(opponent_arg=opponent_arg)
                except KeyError:
                    prompt += f"\n[상대방의 주장]\n{opponent_arg}\n"
            
        return prompt

    def _format_data_context(self, data: Dict[str, Any]) -> str:
        """
        Data Dict를 프롬프트에 삽입할 텍스트로 변환 (기존 로직 + YAML Base Summary)
        """
        base_summary_tpl = self.prompts.get("debate_agents", {}).get("base", {}).get("data_summary", "")
        
        # 기본 요약 생성
        summary = base_summary_tpl.format(
            query=data.get("query", "알 수 없음"),
            event_count=len(data.get("events", [])),
            recent_event_count=0, # TODO: 최근 필터 구현
            trend_count=len(data.get("trends", [])),
            metric_count=len(data.get("metrics", [])),
            path_count=len(data.get("impact_paths", []))
        )
        
        details = []
        
        # 데이터 리스팅
        # 1. Events (NULL 안전성 강화)
        events = data.get("events", [])
        if events:
            details.append("\n### Events (이벤트)")
            for e in events[:5]:
                name = e.get('name', 'Unknown')
                desc = e.get('description', 'N/A')
                details.append(f"- {name}: {desc}")
                
        # 2. Trends
        trends = data.get("trends", [])
        if trends:
            details.append("\n### Trends (트렌드)")
            for t in trends[:3]:
                details.append(f"- {t.get('name', 'Unknown')}")
                 
        # 3. Metrics (NULL 안전성 강화)
        metrics = data.get("metrics", [])
        if metrics:
            details.append("\n### Metrics (지표)")
            for m in metrics[:5]:
                val = m.get('properties', {}).get('value', 'N/A')
                name = m.get('name', 'Unknown')
                details.append(f"- {name}: {val}")

        # 4. Impact Paths (Cognitive Filtering의 핵심)
        impact_paths = data.get("impact_paths", [])
        if impact_paths:
            details.append("\n### Impact Paths (인과 경로)")
            for i, p in enumerate(impact_paths[:10]):
                details.append(f"- [Path {i+1}] {p.get('text', 'N/A')}")
                
        return summary + "\n".join(details)
        
    def _parse_response(self, response: Any) -> Dict[str, str]:
        """LLM 응답 처리 (단순 텍스트 반환)"""
        if hasattr(response, "content"):
             return {"argument": response.content}
        return {"argument": str(response)}
