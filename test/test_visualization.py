
import os
import sys
import traceback
from unittest.mock import MagicMock

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 로그 파일 설정
log_file = "test_vis_debug.log"

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

try:
    log("=== Starting Visualization Test ===")
    from src.agents.synthesizer_agent import SynthesizerAgent
    from src.utils.visualizer import MatplotlibVisualizer
    log("Imports successful.")
except Exception as e:
    log(f"Import Error: {e}")
    traceback.print_exc(file=open(log_file, "a", encoding="utf-8"))
    sys.exit(1)

def test_visualization_generation():
    try:
        # 1. Mock LLM & Agent Setup
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Report Content"
        
        agent = SynthesizerAgent(llm=mock_llm)
        log("Agent initialized.")
        
        # 2. Mock State
        state = {
            "query": "Samsung Electronics",
            "debate_state": {
                "bull_history": "History",
                "bear_history": "History"
            },
            "judge_verdict": {
                "decision": "BUY",
                "score": 85,
                "confidence_level": "High",
                "rationale": "Rationale",
                "winning_side": "Bull",
                "bull_score": 80,
                "bear_score": 40
            }
        }
        
        # 3. Execute synthesize
        log("Running synthesize...")
        report = agent.synthesize(state)
        log(f"Report generated. Length: {len(report)}")
        
        # 4. Verify Files
        charts_dir = "data/outputs/charts"
        expected_files = ["debate_score.png", "financial_trend.png"]
        
        all_exist = True
        for f in expected_files:
            path = os.path.join(charts_dir, f)
            if os.path.exists(path):
                log(f"✅ Created: {path}")
            else:
                log(f"❌ Missing: {path}")
                all_exist = False
                
        if all_exist:
            log("ALL SUCCESS")
        else:
            log("SOME FILES MISSING")
            
    except Exception as e:
        log(f"Runtime Error: {e}")
        traceback.print_exc(file=open(log_file, "a", encoding="utf-8"))

if __name__ == "__main__":
    if os.path.exists(log_file):
        os.remove(log_file)
    test_visualization_generation()
