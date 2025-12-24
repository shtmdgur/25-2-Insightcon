# Judge Agent

## 역할
**Bull vs Bear 토론을 평가하고 최종 투자의견 도출**

## 프로세스

```
Bull/Bear 3라운드 토론 → Judge 평가 → Verdict 출력
```

| 단계 | 내용 |
|------|------|
| 입력 | Bull/Bear 토론 이력 + Knowledge Graph 인과경로 |
| 평가 | LLM이 논거 품질 & 증거 신뢰도 검증 |
| 출력 | `decision` (BUY/SELL/HOLD) + `score` (0-100) + `key_factors` |

## 출력 예시

```json
{
  "decision": "BUY",
  "score": 75,
  "winning_side": "Bull",
  "key_factors": ["HBM 수요 급증", "AI 시장 선점"]
}
```

## 특징
- **Cognitive Filtering**: LLM이 맥락 기반 증거 선별
- **중립성**: 토론 참여 X, 판결만 수행
