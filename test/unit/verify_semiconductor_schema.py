import sys
import os
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.nodes import NodeType, RelationType, ENTITY_TYPE_PROPERTIES

def verify_schema():
    print("=== Verifying Semiconductor Ontology T-Box 2.0 ===")
    
    # 1. Verify NodeTypes
    print(f"\n[NodeType Check]")
    print(f"Total NodeTypes: {len(NodeType)}")
    if len(NodeType) < 58:
        print(f"WARNING: Expected around 58 NodeTypes, found {len(NodeType)}")
    else:
        print(f"PASS: Node count ({len(NodeType)}) appears correct.")
        
    required_nodes = ["Observation", "TemporalRegion", "IDM", "Fabless", "SemiconductorEntity"]
    for node in required_nodes:
        found = any(n.value == node for n in NodeType)
        status = "PASS" if found else "FAIL"
        print(f"  - {node}: {status}")

    # 2. Verify RelationTypes
    print(f"\n[RelationType Check]")
    print(f"Total RelationTypes: {len(RelationType)}")
    if len(RelationType) < 21:
        print(f"WARNING: Expected around 21 RelationTypes, found {len(RelationType)}")
    else:
        print(f"PASS: Relation count ({len(RelationType)}) appears correct.")
        
    required_relations = ["recordedAt", "observes", "hasValue", "participatesIn"]
    for rel in required_relations:
        found = any(r.value == rel for r in RelationType)
        status = "PASS" if found else "FAIL"
        print(f"  - {rel}: {status}")

    # 3. Verify Properties
    print(f"\n[Property Definition Check]")
    missing_props = []
    for node in NodeType:
        if node not in ENTITY_TYPE_PROPERTIES:
            missing_props.append(node.value)
    
    if missing_props:
        print(f"WARNING: Missing properties for: {missing_props}")
    else:
        print("PASS: All NodeTypes have property definitions.")
        
    # 4. Check Observation Properties
    obs_props = ENTITY_TYPE_PROPERTIES.get(NodeType.OBSERVATION)
    if "date" in obs_props and "value" in obs_props:
        print("PASS: Observation has 'date' and 'value' properties.")
    else:
        print(f"FAIL: Observation properties incomplete: {obs_props}")

if __name__ == "__main__":
    verify_schema()
