from src.models.nodes import Entity, Relation, NodeType, RelationType, validate_relation
import pytest

def test_validate_relation_affects():
    # Valid AFFECTS relation
    rel = Relation(
        subject="USD/KRW",
        subject_type=NodeType.ECONOMIC_INDICATOR,
        predicate=RelationType.AFFECTS,
        object="삼성전자",
        object_type=NodeType.IDM,
        correlation="DIRECT"
    )
    assert validate_relation(rel) is True

def test_validate_relation_triggered_by():
    # Valid TRIGGERED_BY relation
    rel = Relation(
        subject="PriceMovement_ABC",
        subject_type=NodeType.PRICE_MOVEMENT,
        predicate=RelationType.TRIGGERED_BY,
        object="Earnings_ABC",
        object_type=NodeType.EARNINGS
    )
    assert validate_relation(rel) is True

if __name__ == "__main__":
    test_validate_relation_affects()
    test_validate_relation_triggered_by()
    print("Core model validation tests passed!")
