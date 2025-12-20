"""
온톨로지 동기화 스크립트

nodes.py의 Enum 정의를 prompts.yaml에 자동 반영합니다.
"""
from pathlib import Path
from typing import List
import yaml

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
NODES_FILE = PROJECT_ROOT / "src" / "models" / "nodes.py"
PROMPTS_FILE = PROJECT_ROOT / "src" / "templates" / "prompts.yaml"


def extract_enum_members(enum_name: str) -> List[str]:
    """
    nodes.py에서 Enum 멤버 추출
    
    Args:
        enum_name: 'NodeType' 또는 'RelationType'
    
    Returns:
        Enum 값 리스트
    """
    with open(NODES_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Enum 정의 파싱
    members = []
    in_enum = False
    
    for line in content.split('\n'):
        # Enum 시작 감지
        if f'class {enum_name}(str, Enum):' in line:
            in_enum = True
            continue
        
        # Enum 종료 감지 (다음 class 또는 빈 줄)
        if in_enum and (line.startswith('class ') or line.strip() == ''):
            break
        
        # Enum 멤버 추출
        if in_enum and '=' in line:
            # 예: OBSERVATION = "Observation"
            parts = line.strip().split('=')
            if len(parts) == 2:
                value = parts[1].strip().strip('"\'')
                members.append(value)
    
    return members


def generate_ontology_prompt_section() -> str:
    """
    prompts.yaml에 삽입할 온톨로지 섹션 생성
    
    Returns:
        YAML 형식 문자열
    """
    node_types = extract_enum_members('NodeType')
    relation_types = extract_enum_members('RelationType')
    
    prompt_section = f"""
      # 1. Ontology Schema (Strictly Follow)

      ## Node Types (Entities)
      Identify entities and classify them into one of these types:
      
"""
    
    # NodeType 리스트 생성 (10개씩 줄바꿈)
    for i, node_type in enumerate(node_types, 1):
        prompt_section += f"      - `{node_type}`"
        if i % 10 == 0:
            prompt_section += "\n"
        else:
            prompt_section += ", "
    
    prompt_section += f"""

      ## Relation Types
"""
    
    # RelationType 리스트 생성
    for i, rel_type in enumerate(relation_types, 1):
        prompt_section += f"      - `{rel_type}`"
        if i % 10 == 0:
            prompt_section += "\n"
        else:
            prompt_section += ", "
    
    return prompt_section


def update_prompts_yaml():
    """
    prompts.yaml 파일 업데이트
    
    gemini_pdf_parser.kg_extraction.instruction의 
    Ontology Schema 섹션을 자동 생성된 내용으로 교체
    """
    # YAML 파일 로드
    with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    
    # 온톨로지 섹션 생성
    ontology_section = generate_ontology_prompt_section()
    
    # instruction 가져오기
    current_instruction = prompts['gemini_pdf_parser']['kg_extraction']['instruction']
    
    # Ontology Schema 섹션 교체
    # (START_MARKER와 END_MARKER 사이 내용 교체)
    START_MARKER = "# 1. Ontology Schema (Strictly Follow)"
    END_MARKER = "# 2. Key Extraction Rules"
    
    if START_MARKER in current_instruction and END_MARKER in current_instruction:
        before = current_instruction.split(START_MARKER)[0]
        after = current_instruction.split(END_MARKER)[1]
        
        new_instruction = before + ontology_section + "\n      " + END_MARKER + after
        prompts['gemini_pdf_parser']['kg_extraction']['instruction'] = new_instruction
        
        # YAML 저장
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(prompts, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        print(f"✅ prompts.yaml 업데이트 완료")
        print(f"   - Node Types: {len(extract_enum_members('NodeType'))}개")
        print(f"   - Relation Types: {len(extract_enum_members('RelationType'))}개")
    else:
        print("❌ Ontology Schema 마커를 찾을 수 없습니다.")
        print(f"   START_MARKER: {START_MARKER in current_instruction}")
        print(f"   END_MARKER: {END_MARKER in current_instruction}")


if __name__ == "__main__":
    print("🔄 온톨로지 동기화 시작...")
    update_prompts_yaml()
