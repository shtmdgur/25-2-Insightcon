"""
문서 로더 유틸리티
파일 경로를 받아서 텍스트로 변환하는 기능 제공
"""
from pathlib import Path
from typing import Union, Optional


def load_document(document_input: Union[str, Path, None]) -> Optional[str]:
    """
    문서 입력을 텍스트로 변환
    
    Args:
        document_input: 
            - 문자열 텍스트: 그대로 반환
            - 파일 경로 (str 또는 Path): 파일을 읽어서 텍스트로 변환
            - None: None 반환
    
    Returns:
        문서 텍스트 (문자열) 또는 None
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 지원하지 않는 파일 형식일 때
    """
    # None이거나 빈 문자열이면 None 반환
    if not document_input:
        return None
    
    # 이미 문자열이고 파일 경로가 아닌 경우 (파일 존재 여부 확인)
    if isinstance(document_input, str):
        # 파일 경로인지 확인 (파일이 존재하는지 체크)
        file_path = Path(document_input)
        
        # 파일이 존재하면 파일로 처리
        if file_path.exists() and file_path.is_file():
            return _load_file(file_path)
        else:
            # 파일이 없으면 일반 텍스트로 처리
            return document_input
    
    # Path 객체인 경우
    elif isinstance(document_input, Path):
        if document_input.exists() and document_input.is_file():
            return _load_file(document_input)
        else:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {document_input}")
    
    else:
        raise ValueError(f"지원하지 않는 입력 형식: {type(document_input)}")


def _load_file(file_path: Path) -> str:
    """
    파일을 읽어서 텍스트로 변환
    
    Args:
        file_path: 파일 경로
    
    Returns:
        파일 내용 (텍스트)
    
    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        ValueError: 지원하지 않는 파일 형식일 때
    """
    if not file_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"파일이 아닙니다: {file_path}")
    
    # 파일 확장자 확인
    suffix = file_path.suffix.lower()
    
    # 마크다운 파일 (.md)
    if suffix == '.md':
        return _load_text_file(file_path)
    
    # 텍스트 파일 (.txt)
    elif suffix == '.txt':
        return _load_text_file(file_path)
    
    # PDF 파일 (.pdf)
    elif suffix == '.pdf':
        return _load_pdf_file(file_path)
    
    else:
        # 확장자가 없거나 알 수 없는 경우 텍스트 파일로 시도
        try:
            return _load_text_file(file_path)
        except UnicodeDecodeError:
            raise ValueError(
                f"지원하지 않는 파일 형식: {suffix}. "
                f"지원 형식: .md, .txt, .pdf"
            )


def _load_text_file(file_path: Path) -> str:
    """텍스트 파일 읽기 (마크다운, 일반 텍스트)"""
    try:
        # UTF-8로 시도
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # UTF-8 실패 시 CP949 (한글 윈도우 기본 인코딩)로 시도
        try:
            with open(file_path, 'r', encoding='cp949') as f:
                return f.read()
        except UnicodeDecodeError:
            # 마지막으로 latin-1로 시도 (거의 모든 바이트를 읽을 수 있음)
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()


def _load_pdf_file(file_path: Path) -> str:
    """PDF 파일을 마크다운으로 변환"""
    try:
        import pymupdf4llm
    except ImportError:
        raise ImportError(
            "PDF 파일을 읽으려면 pymupdf4llm이 필요합니다. "
            "다음 명령어로 설치하세요: pip install pymupdf4llm"
        )
    
    # PDF를 마크다운으로 변환
    md_text = pymupdf4llm.to_markdown(str(file_path), write_images=False)
    return md_text
