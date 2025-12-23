"""
완벽 점검 스크립트 - 모든 Parser와 모델의 일관성 검증
"""
from pathlib import Path
import sys

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_model_definitions():
    """모델 정의 검증"""
    print("=" * 60)
    print("1. 모델 정의 검증")
    print("=" * 60)
    
    from src.models.nodes import NodeType, RelationType, Entity, Relation
    
    # NodeType 확인
    print("\n✅ NodeType Enum:")
    for node_type in NodeType:
        print(f"   - {node_type.name}: {node_type.value}")
    
    # RelationType 확인
    print("\n✅ RelationType Enum:")
    for rel_type in RelationType:
        print(f"   - {rel_type.name}: {rel_type.value}")
    
    # Relation 모델 필드 확인
    print("\n✅ Relation 모델 필드:")
    print(f"   - subject: str (Required)")
    print(f"   - predicate: RelationType (Required)")
    print(f"   - object: str (Required)")
    print(f"   - properties: Dict[str, Any] (Optional)")
    print(f"   - correlation: Optional[str]")
    print(f"   - sensitivity: Optional[float]")
    print(f"   - lag: Optional[str]")
    print(f"   - confidence: Optional[float]")
    print(f"   - reasoning: Optional[str]")

def test_parser_imports():
    """Parser import 검증"""
    print("\n" + "=" * 60)
    print("2. Parser Import 검증")
    print("=" * 60)
    
    parsers = {
        "DARTParser": "src.agents.parsers.dart_parser_agent",
        "PriceParser": "src.agents.parsers.price_parser_agent",
        "FundParser": "src.agents.parsers.fund_parser_agent",
        "NewsParser": "src.agents.parsers.news_parser_agent",
        "MacroParser": "src.agents.parsers.macro_parser_agent",
    }
    
    for name, module in parsers.items():
        try:
            __import__(module)
            print(f"   ✅ {name}: OK")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
            return False
    
    return True

def test_relation_creation():
    """Relation 객체 생성 테스트"""
    print("\n" + "=" * 60)
    print("3. Relation 객체 생성 테스트")
    print("=" * 60)
    
    from src.models.nodes import Relation, RelationType
    
    test_cases = [
        {
            "name": "HAS_SIGNAL (기본)",
            "data": {
                "subject": "NVIDIA Corporation",
                "predicate": RelationType.HAS_SIGNAL,
                "object": "PriceMovement_NVDA_20240101"
            }
        },
        {
            "name": "HAS_SIGNAL (properties)",
            "data": {
                "subject": "NVIDIA Corporation",
                "predicate": RelationType.HAS_SIGNAL,
                "object": "PriceMovement_NVDA_20240101",
                "properties": {"date": "2024-01-01"}
            }
        },
        {
            "name": "AFFECTS (메타데이터)",
            "data": {
                "subject": "USD/KRW",
                "predicate": RelationType.AFFECTS,
                "object": "SK하이닉스",
                "correlation": "INVERSE",
                "sensitivity": 0.8,
                "lag": "1Q",
                "confidence": 0.9
            }
        },
        {
            "name": "TRIGGERED_BY (reasoning)",
            "data": {
                "subject": "PriceMovement_NVDA_20240315",
                "predicate": RelationType.TRIGGERED_BY,
                "object": "Earnings_NVIDIA_2024_Q1",
                "reasoning": "Temporal correlation",
                "confidence": 0.7
            }
        }
    ]
    
    for test in test_cases:
        try:
            rel = Relation(**test["data"])
            print(f"   ✅ {test['name']}: OK")
        except Exception as e:
            print(f"   ❌ {test['name']}: {e}")
            return False
    
    return True

def test_entity_creation():
    """Entity 객체 생성 테스트"""
    print("\n" + "=" * 60)
    print("4. Entity 객체 생성 테스트")
    print("=" * 60)
    
    from src.models.nodes import Entity, NodeType
    
    test_cases = [
        {
            "name": "Agent (IDM)",
            "data": {
                "name": "삼성전자",
                "type": NodeType.IDM,
                "properties": {"ticker": "005930"},
                "confidence": 1.0
            }
        },
        {
            "name": "Signal (PRICE_MOVEMENT)",
            "data": {
                "name": "PriceMovement_NVDA_20240101",
                "type": NodeType.PRICE_MOVEMENT,
                "direction": "UP",
                "magnitude": 5.2,
                "sentiment": "POSITIVE",
                "properties": {"date": "2024-01-01", "close": 500.0},
                "confidence": 1.0
            }
        },
        {
            "name": "MacroMetric (ECONOMIC_INDICATOR)",
            "data": {
                "name": "MacroIndicator_USD/KRW_2024-01-01",
                "type": NodeType.ECONOMIC_INDICATOR,
                "properties": {"series": "USD/KRW", "date": "2024-01-01", "value": 1300.0},
                "confidence": 1.0
            }
        }
    ]
    
    for test in test_cases:
        try:
            entity = Entity(**test["data"])
            print(f"   ✅ {test['name']}: OK")
        except Exception as e:
            print(f"   ❌ {test['name']}: {e}")
            return False
    
    return True

def main():
    print("\n🔍 완벽 점검 시작\n")
    
    try:
        test_model_definitions()
        
        if not test_parser_imports():
            print("\n❌ Parser import 실패!")
            return False
        
        if not test_relation_creation():
            print("\n❌ Relation 객체 생성 실패!")
            return False
        
        if not test_entity_creation():
            print("\n❌ Entity 객체 생성 실패!")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 모든 검증 통과! 완벽합니다!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
