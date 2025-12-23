import json

# JSON 파일의 처음 5개만 읽기
with open('neo4j_query_table_data_2025-12-22.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"✅ 총 경로 수: {len(data):,}개")
print()
print("=" * 80)
print("처음 5개 경로 상세 분석")
print("=" * 80)

for i, item in enumerate(data[:5], 1):
    print(f"\n📍 경로 {i}")
    print("-" * 80)
    
    # START 노드
    start_node = item['p']['start']
    start_labels = start_node['labels']
    start_name = start_node['properties'].get('name', 'Unknown')
    start_ticker = start_node['properties'].get('ticker', 'N/A')
    
    print(f"  START: [{', '.join(start_labels)}] {start_name}")
    print(f"         Ticker: {start_ticker}")
    
    # Relationship
    if item['p']['segments']:
        rel = item['p']['segments'][0]['relationship']
        rel_type = rel['type']
        print(f"  REL:   -{rel_type}->")
    
    # END 노드
    end_node = item['p']['end']
    end_labels = end_node['labels']
    end_name = end_node['properties'].get('name', 'Unknown')
    
    print(f"  END:   [{', '.join(end_labels)}] {end_name}")
    
    # PriceMovement 체크
    all_labels = start_labels + end_labels
    has_price = any('Price' in label or 'Movement' in label for label in all_labels)
    if has_price:
        print(f"  ⚠️  PriceMovement 발견!")
    else:
        print(f"  ✅  PriceMovement 없음")

print()
print("=" * 80)
print("전체 통계 요약")
print("=" * 80)

# 전체 노드 타입 카운트
from collections import Counter
start_types = Counter()
end_types = Counter()
rel_types = Counter()

for item in data:
    for label in item['p']['start']['labels']:
        start_types[label] += 1
    for label in item['p']['end']['labels']:
        end_types[label] += 1
    if item['p']['segments']:
        rel_types[item['p']['segments'][0]['relationship']['type']] += 1

print("\n🎯 START 노드 타입 (상위 10개)")
for label, count in start_types.most_common(10):
    print(f"  {label:25s}: {count:>4,}")

print("\n🎯 END 노드 타입 (상위 10개)")
for label, count in end_types.most_common(10):
    print(f"  {label:25s}: {count:>4,}")

print("\n🎯 관계 타입")
for rel, count in rel_types.most_common():
    print(f"  {rel:25s}: {count:>4,}")

# PriceMovement 체크
price_count = sum(1 for label in list(start_types.keys()) + list(end_types.keys()) if 'Price' in label or 'Movement' in label)
print()
print("=" * 80)
if price_count == 0:
    print("✅ PriceMovement가 하나도 없습니다! 필터링 성공!")
else:
    print(f"⚠️ PriceMovement 타입 발견: {price_count}개")
print("=" * 80)
