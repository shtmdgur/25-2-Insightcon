import yaml
import os
import logging
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 프로젝트 루트 경로 계산 (src/config/prompt_loader.py -> project_root)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
PROMPT_YAML_PATH = os.path.join(PROJECT_ROOT, "src", "templates", "prompts.yaml")

def load_prompts() -> Dict[str, Any]:
    """
    Load prompts from src/templates/prompts.yaml
    """
    if not os.path.exists(PROMPT_YAML_PATH):
        logger.warning(f"Prompt file not found at {PROMPT_YAML_PATH}")
        return {}

    try:
        with open(PROMPT_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        return {}

# Singleton instance
PROMPTS = load_prompts()

if __name__ == "__main__":
    # Test loading
    print(f"Loaded {len(PROMPTS)} sections.")
    if "debate_agents" in PROMPTS:
        print("Debate Agents config found.")
