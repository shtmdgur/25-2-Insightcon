import json
import os
import glob

# 최신 merged_kg 파일 찾기
files = glob.glob(r'd:\0.Sogang\동아리 및 학회\Insight\2025-2\2차 인사이콘\25-2-Insightcon\data\processed\merged_kg_*.json')
file_path = sorted(files)[-1] if files else ""

print(f"Checking file: {file_path}")

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    entities = data.get('entities', [])
    # 숫자(코드)로 된 엔티티 이름 찾기
    code_named_entities = [e for e in entities if e.get('name', '').isdigit()]
    
    print(f"Total entities: {len(entities)}")
    print(f"Entities with numeric names: {len(code_named_entities)}")
    for e in code_named_entities[:20]:
        print(f"Name: {e.get('name')}, Type: {e.get('type')}, properties: {e.get('properties', {})}")
else:
    print(f"File not found: {file_path}")
