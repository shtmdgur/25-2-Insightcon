import json
from pathlib import Path

def analyze_kg_failures(kg_path: str):
    print(f"Analyzing {kg_path}...")
    with open(kg_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entities = {e['name']: e for e in data.get('entities', [])}
    relations = data.get('relations', [])
    
    print(f"Total Entities: {len(entities)}")
    print(f"Total Relations: {len(relations)}")
    
    missing_subjects = {}
    missing_objects = {}
    missing_relations = []
    for rel in relations:
        s = rel['subject']
        o = rel['object']
        if s not in entities:
            missing_subjects[s] = missing_subjects.get(s, 0) + 1
            missing_relations.append(rel)
        if o not in entities:
            missing_objects[o] = missing_objects.get(o, 0) + 1
            if rel not in missing_relations:
                missing_relations.append(rel)
            
    print(f"\n--- Detailed Missing Relations ({len(missing_relations)} cases) ---")
    for i, rel in enumerate(missing_relations[:100]):
        print(f"{i+1}. [{rel['predicate']}] {rel['subject']} -> {rel['object']}")
            
    print("\n--- Top Missing Subjects (Node names that don't exist as Entities) ---")
    sorted_s = sorted(missing_subjects.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_s[:20]:
        print(f"[{count}] {name}")
        
    print("\n--- Top Missing Objects (Node names that don't exist as Entities) ---")
    sorted_o = sorted(missing_objects.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_o[:20]:
        print(f"[{count}] {name}")

    # 구체적인 원인 추적을 위한 샘플링
    print("\n--- Potential Reason: Numerical Corp Codes in Subjects but Names in Entities ---")
    sk_hynix_id = "00160843"
    if sk_hynix_id in missing_subjects:
        print(f"Found {missing_subjects[sk_hynix_id]} relations starting from '{sk_hynix_id}'.")
        # 엔티티 리스트에 "SK하이닉스"가 있는지 확인
        sk_hynix_entity = [n for n in entities.keys() if "SK하이닉스" in n]
        print(f"Entities containing 'SK하이닉스': {sk_hynix_entity}")

if __name__ == "__main__":
    kg_path = r"d:\0.Sogang\동아리 및 학회\Insight\2025-2\2차 인사이콘\25-2-Insightcon\data\merged_kg_20251223_2259.json"
    analyze_kg_failures(kg_path)
