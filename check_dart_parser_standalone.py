import sys
from pathlib import Path
import pandas as pd
import logging

# 프로젝트 루트 추가
project_root = Path(r'd:\0.Sogang\동아리 및 학회\Insight\2025-2\2차 인사이콘\25-2-Insightcon')
sys.path.insert(0, str(project_root))

from src.agents.parsers.dart_parser_agent import DARTParserAgent

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)

agent = DARTParserAgent()
dart_dir = project_root / 'data' / 'preprocessed' / 'dart'

print(f"Testing DART parser on: {dart_dir}")
kg = agent.parse(dart_dir)

print(f"\nTotal relations: {len(kg.relations)}")
has_signals = [r for r in kg.relations if r.predicate.value == 'HAS_SIGNAL']
print(f"HAS_SIGNAL relations: {len(has_signals)}")

for r in has_signals[:20]:
    print(f"Subject: {r.subject}, Predicate: {r.predicate}, Object: {r.object}")
