"""Merged KG 분석 스크립트"""
import json
from pathlib import Path
from collections import Counter

import sys

# JSON 로드
if len(sys.argv) > 1:
    kg_path = Path(sys.argv[1])
else:
    # 폴백: 최신 파일 자동 검색
    processed_dir = Path("data/processed")
    files = sorted(processed_dir.glob("merged_kg_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not files:
        print("❌ No merged KG files found in data/processed/")
        sys.exit(1)
    kg_path = files[0]

print(f"🔍 Analyzing: {kg_path}")
with open(kg_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

entities = data['entities']
relations = data['relations']

print("=" * 60)
print("MERGED KG 분석 결과")
print("=" * 60)

# 엔티티 타입별 분포
entity_types = Counter([e['type'] for e in entities])
print("\n📊 Entity 타입별 분포:")
for t, count in entity_types.most_common():
    print(f"  - {t}: {count}개")

print(f"\n총 Entities: {len(entities)}개")
print(f"총 Relations: {len(relations)}개")

# 관계 타입별 분포
relation_types = Counter([r['predicate'] for r in relations])
print("\n🔗 Relation 타입별 분포:")
for t, count in relation_types.most_common():
    print(f"  - {t}: {count}개")

# 샘플 엔티티 (Agent Layer)
print("\n📌 Agent Layer 샘플 (IDM/Fabless/Foundry/Supplier/OSAT/ETC):")
agent_types = ['IDM', 'Fabless', 'Foundry', 'Supplier', 'OSAT', 'ETC']
for e in entities:
    if e['type'] in agent_types:
        # v3.1: 마스터 데이터 정규화 여부 확인 속성이 다를 수 있으므로 일반 출력
        print(f"  - {e['name']} ({e['type']})")

# 샘플 관계 (HAS_SIGNAL)
print("\n🔗 HAS_SIGNAL 관계 샘플:")
has_signal_rels = [r for r in relations if r['predicate'] == 'HAS_SIGNAL']
for r in has_signal_rels[:10]:
    obj_short = r['object'][:40] + '...' if len(r['object']) > 40 else r['object']
    print(f"  - {r['subject']} -> {obj_short}")

# Issue 노드 샘플
print("\n📰 Issue 노드 샘플:")
issues = [e for e in entities if e['type'] == 'Issue']
for issue in issues[:10]:
    title = issue.get('properties', {}).get('title', issue['name'])[:60]
    print(f"  - {issue['name'][:50]}...")
    if issue.get('sentiment'):
        print(f"    Sentiment: {issue['sentiment']}")
