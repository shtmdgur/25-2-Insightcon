
import sys
import os
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Project Root Setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Force UTF-8 Output (Windows mitigation)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Environment Setup
from dotenv import load_dotenv
load_dotenv()

# Logger Setup
import logging
logging.basicConfig(level=logging.INFO)

# Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from src.pipeline.debate_workflow import create_debate_workflow
from src.agents.bull_agent import BullAgent
from src.agents.bear_agent import BearAgent
from src.agents.judge_agent import JudgeAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.pipeline.state import ReportState
import src.pipeline.price_nodes # Ensure module is loaded for patching

# Fix OpenMP Conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Helper to print colored text
def print_header(title):
    print(f"\n{'='*80}")
    print(f"🚀 {title}")
    print(f"{'='*80}")

def mock_price_node(state: ReportState) -> ReportState:
    """Mock Price Load Node"""
    print("💰 [Mock] Price Data Loaded")
    state["price_context"] = {
        "dates": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "prices": [70000, 75000, 80000],
        "volume": [1000000, 1500000, 1200000],
        "summary": "Recent uptrend with increasing volume."
    }
    state["market_context"] = "Market Context: Recent uptrend observed. Volume increasing. Positive momentum."
    return state

def mock_should_continue(state: ReportState):
    """Force stop after 1 round for testing"""
    count = state["debate_state"].get("debate_count", 0)
    if count >= 1: # Stop after 1 round
        return "judge"
    return "continue"

def main():
    print_header("Mid-to-End Pipeline Test (Debate -> Report)")

    # 1. Setup Mock Neo4j
    mock_neo4j = MagicMock()
    
    # 2. Setup Real LLM (or Mock if API key missing)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found. Using Mock LLM.")
        llm = MagicMock()
        llm.invoke.return_value.content = "Mock LLM Response"
    else:
        print("✅ Real LLM Initialized (gemini-3-pro-preview)")
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-pro-preview", 
            google_api_key=api_key,
            temperature=0.7 
        )

    # 3. Initialize Agents
    bull = BullAgent(llm, mock_neo4j)
    bear = BearAgent(llm, mock_neo4j)
    judge = JudgeAgent(llm)
    synthesizer = SynthesizerAgent(llm, mock_neo4j)

    # 4. Create Workflow
    # We need to patch the internal functions of 'create_debate_workflow' 
    # OR we can just use the real one and patch the imported modules it relies on if needed.
    # Here we will patch 'src.pipeline.price_nodes.load_price_context_node'
    # and 'src.pipeline.debate_workflow.should_continue_debate' logic?
    # Modifying internal logic of a compiled graph is hard.
    # Instead, we will monkeypatch the functions BEFORE validation.
    
    with patch("src.pipeline.price_nodes.load_price_context_node", side_effect=mock_price_node) as mock_price:
         
        workflow = create_debate_workflow(bull, bear, judge, synthesizer)

    # 5. Prepare Initial State (Start from "Middle")
    initial_state = {
        "query": "삼성전자",
        "ticker": "005930",
        "impact_paths": [
            "[HBM3e 공급] -> [DRAM 매출 증가] -> [영업이익 개선]",
            "[파운드리 수율 문제] -> [비메모리 적자 지속] -> [전사 이익 훼손]"
        ],
        "graphrag_results": {
            "text_context": "삼성전자는 최근 HBM3e 12단 제품의 엔비디아 퀄 테스트를 진행 중이며, 3분기 내 통과가 유력하다. 반면 파운드리 사업부는 수율 안정화에 어려움을 겪고 있다." 
        },
        "debate_state": None, 
        "retry_count": 0,
        "errors": []
    }

    print_header("Executing Workflow")
    try:
        final_state = workflow.invoke(initial_state)
        
        print_header("Execution Complete")
        
        # 6. Verify Outputs
        print(f"Debate Rounds: {final_state['debate_state']['debate_count']}")
        print(f"Visual Charts Injected: {'True' if 'data/outputs/charts' in str(final_state.get('final_report')) else 'False'}")
        
        # Save Final Report
        with open("final_report_test_mid_end.md", "w", encoding="utf-8") as f:
            f.write(final_state["final_report"])
            
        print(f"✅ Final Report Saved to: {os.path.abspath('final_report_test_mid_end.md')}")
        
    except Exception as e:
        print(f"❌ Execution Failed: {e}")
        import traceback
        with open("error_trace.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()

if __name__ == "__main__":
    main()
