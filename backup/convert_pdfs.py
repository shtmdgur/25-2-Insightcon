"""
PDF를 마크다운으로 변환하여 커서가 학습할 수 있도록 하는 스크립트
개인적으로 pymupdf4llm을 설치해서 사용하는 독립 스크립트
"""
import os
import sys
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("오류: pymupdf4llm이 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install pymupdf4llm")
    sys.exit(1)


def pdf_to_markdown(pdf_path: Path, output_dir: Path, write_images: bool = False) -> str:
    """
    PDF 파일을 마크다운으로 변환합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        output_dir: 마크다운 파일을 저장할 디렉토리
        write_images: 이미지를 추출할지 여부
    
    Returns:
        변환된 마크다운 텍스트
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 출력 파일명
    output_filename = pdf_path.stem + ".md"
    output_path = output_dir / output_filename
    
    # PDF를 마크다운으로 변환
    print(f"  변환 중: {pdf_path.name}...")
    md_text = pymupdf4llm.to_markdown(
        str(pdf_path),
        write_images=write_images
    )
    
    # 마크다운 파일 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    
    return str(output_path)


def main():
    """참고 자료 폴더의 모든 PDF를 마크다운으로 변환"""
    # 현재 스크립트 위치 기준으로 경로 설정
    script_dir = Path(__file__).parent
    pdf_dir = script_dir / "참고 자료"  # parent 제거 - 같은 디렉토리
    output_dir = script_dir / "25-2-Insightcon" / "data" / "processed" / "pdf_markdown"
    
    print("=" * 60)
    print("PDF → Markdown 변환 시작")
    print("=" * 60)
    print(f"PDF 디렉토리: {pdf_dir}")
    print(f"출력 디렉토리: {output_dir}")
    print("-" * 60)
    
    if not pdf_dir.exists():
        print(f"오류: PDF 디렉토리를 찾을 수 없습니다: {pdf_dir}")
        sys.exit(1)
    
    # PDF 파일 찾기
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"PDF 파일을 찾을 수 없습니다: {pdf_dir}")
        sys.exit(1)
    
    print(f"총 {len(pdf_files)}개의 PDF 파일을 찾았습니다.\n")
    
    converted_files = []
    failed_files = []
    
    for pdf_file in pdf_files:
        try:
            output_path = pdf_to_markdown(pdf_file, output_dir, write_images=False)
            converted_files.append(output_path)
            print(f"  ✓ 완료: {pdf_file.name} → {Path(output_path).name}")
        except Exception as e:
            failed_files.append((pdf_file.name, str(e)))
            print(f"  ✗ 오류 ({pdf_file.name}): {e}")
        print()
    
    # 결과 요약
    print("-" * 60)
    print(f"✓ 성공: {len(converted_files)}개")
    if failed_files:
        print(f"✗ 실패: {len(failed_files)}개")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    print("-" * 60)
    print(f"변환된 파일들은 {output_dir}에 저장되었습니다.")
    print("커서가 이제 이 마크다운 파일들을 학습할 수 있습니다!")


if __name__ == "__main__":
    main()
