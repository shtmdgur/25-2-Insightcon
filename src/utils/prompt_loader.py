"""
Prompt 템플릿 로더

prompts.yaml 파일에서 에이전트별 프롬프트를 로드합니다.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptTemplateLoader:
    """YAML 기반 프롬프트 템플릿 로더"""
    
    def __init__(self, template_path: str = "src/templates/prompts.yaml"):
        """
        Args:
            template_path: prompts.yaml 파일 경로
        """
        self.template_path = Path(template_path)
        self._templates: Optional[Dict[str, Any]] = None
    
    def load(self) -> Dict[str, Any]:
        """
        YAML 파일 로드
        
        Returns:
            프롬프트 템플릿 딕셔너리
        """
        if self._templates is not None:
            return self._templates
        
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self._templates = yaml.safe_load(f)
            
            logger.info(f"Loaded prompt templates from {self.template_path}")
            return self._templates
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {e}")
            raise RuntimeError(f"YAML parsing error: {e}")
    
    def get_analyst_prompt(self, analyst_type: str) -> Dict[str, str]:
        """
        분석가 프롬프트 가져오기
        
        Args:
            analyst_type: 'fundamentals', 'trend', 'events'
        
        Returns:
            프롬프트 딕셔너리 (role, goal, instruction)
        """
        templates = self.load()
        
        if 'analysts' not in templates:
            raise KeyError("'analysts' section not found in prompts.yaml")
        
        if analyst_type not in templates['analysts']:
            raise KeyError(f"Analyst type '{analyst_type}' not found")
        
        return templates['analysts'][analyst_type]
    
    def get_debate_prompt(self, stance: str) -> Dict[str, str]:
        """
        토론 프롬프트 가져오기
        
        Args:
            stance: 'bull' or 'bear'
        
        Returns:
            프롬프트 딕셔너리
        """
        templates = self.load()
        
        if 'debate' not in templates:
            raise KeyError("'debate' section not found in prompts.yaml")
        
        if stance not in templates['debate']:
            raise KeyError(f"Debate stance '{stance}' not found")
        
        return templates['debate'][stance]
    
    def get_synthesizer_prompt(self) -> Dict[str, str]:
        """
        종합 프롬프트 가져오기
        
        Returns:
            프롬프트 딕셔너리
        """
        templates = self.load()
        
        if 'synthesizer' not in templates:
            raise KeyError("'synthesizer' section not found in prompts.yaml")
        
        return templates['synthesizer']


# 싱글톤 인스턴스
_prompt_loader: Optional[PromptTemplateLoader] = None


def get_prompt_loader() -> PromptTemplateLoader:
    """
    PromptTemplateLoader 싱글톤 인스턴스 반환
    
    Returns:
        PromptTemplateLoader 인스턴스
    """
    global _prompt_loader
    
    if _prompt_loader is None:
        _prompt_loader = PromptTemplateLoader()
    
    return _prompt_loader
