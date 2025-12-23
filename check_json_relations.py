import json
import os

file_path = r'd:\0.Sogang\동아리 및 학회\Insight\2025-2\2차 인사이콘\25-2-Insightcon\data\processed\merged_kg_20251223_2347.json'

if os.path.exists(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    relations = data.get('relations', [])
    has_signals = [r for r in relations if r.get('predicate') == 'HAS_SIGNAL']
    
    print(f"Total HAS_SIGNAL relations: {len(has_signals)}")
    for r in has_signals[:20]:
        print(f"Subject: {r.get('subject')}, Predicate: {r.get('predicate')}, Object: {r.get('object')}")
else:
    print(f"File not found: {file_path}")
