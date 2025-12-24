"""
리포트 PDF 변환 유틸리티

Markdown 리포트를 PDF로 변환합니다.

의존성:
    pip install weasyprint markdown

사용법:
    from src.utils.report_exporter import ReportExporter
    exporter = ReportExporter()
    pdf_path = exporter.export_to_pdf(markdown_content, "report.pdf")
"""

import os
import sys
import warnings
from pathlib import Path
from datetime import datetime
from typing import Optional

# WeasyPrint 경고 숨기기
warnings.filterwarnings("ignore", message=".*WeasyPrint.*")
os.environ['WEASYPRINT_QUIET'] = '1'

# stderr를 임시로 숨기기 (WeasyPrint 가져올 때)
_original_stderr = sys.stderr
try:
    sys.stderr = open(os.devnull, 'w')
    import weasyprint  # noqa: F401
except ImportError:
    pass
finally:
    sys.stderr = _original_stderr


class ReportExporter:
    """
    리포트 PDF 내보내기
    
    Markdown → HTML → PDF 변환
    """
    
    # PDF 스타일 (증권사 리포트 스타일)
    CSS_STYLE = """
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: counter(page) " / " counter(pages);
            font-size: 10px;
            color: #666;
        }
    }
    
    body {
        font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        font-size: 18pt;
        color: #1a1a1a;
        border-bottom: 2px solid #0066cc;
        padding-bottom: 8px;
        margin-top: 24px;
    }
    
    h2 {
        font-size: 14pt;
        color: #0066cc;
        margin-top: 20px;
    }
    
    h3 {
        font-size: 12pt;
        color: #333;
        margin-top: 16px;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 10pt;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    
    blockquote {
        border-left: 4px solid #0066cc;
        padding-left: 16px;
        margin: 16px 0;
        color: #555;
        font-style: italic;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10pt;
    }
    
    pre {
        background-color: #f4f4f4;
        padding: 12px;
        border-radius: 4px;
        overflow-x: auto;
    }
    
    .mermaid {
        text-align: center;
        margin: 20px 0;
    }
    
    strong {
        color: #0066cc;
    }
    
    .header {
        text-align: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid #ddd;
    }
    
    .header h1 {
        border: none;
        margin: 0;
        padding: 0;
    }
    
    .meta {
        font-size: 10pt;
        color: #666;
        margin-top: 8px;
    }
    """
    
    def __init__(self, output_dir: str = "data/outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_pdf(
        self,
        markdown_content: str,
        filename: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[str]:
        """
        Markdown을 PDF로 변환
        
        Args:
            markdown_content: Markdown 텍스트
            filename: 출력 파일명 (None이면 타임스탬프 기반 생성)
            title: 리포트 제목
        
        Returns:
            생성된 PDF 파일 경로 (실패 시 None)
        """
        try:
            import markdown
            from weasyprint import HTML, CSS
        except ImportError:
            return self._fallback_save_html(markdown_content, filename)
        
        # 파일명 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.pdf"
        
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        
        pdf_path = self.output_dir / filename
        
        # Markdown → HTML 변환
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        # HTML 템플릿 구성
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title or 'Investment Report'}</title>
            <style>{self.CSS_STYLE}</style>
        </head>
        <body>
            <div class="header">
                <h1>{title or 'AI Investment Analysis Report'}</h1>
                <div class="meta">
                    Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 
                    Powered by Multi-Agent Debate System
                </div>
            </div>
            {html_content}
        </body>
        </html>
        """
        
        # PDF 생성
        try:
            HTML(string=full_html).write_pdf(str(pdf_path))
            print(f"✅ PDF 저장: {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            print(f"❌ PDF 생성 실패: {e}")
            return self._fallback_save_html(markdown_content, filename)
    
    def _fallback_save_html(self, markdown_content: str, filename: Optional[str]) -> str:
        """PDF 생성 실패 시 HTML로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}"
        
        html_path = self.output_dir / f"{filename.replace('.pdf', '')}.html"
        md_path = self.output_dir / f"{filename.replace('.pdf', '')}.md"
        
        # Markdown 저장
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"📝 Markdown 저장: {md_path}")
        
        return str(md_path)
    
    def export_from_state(self, state: dict, filename: Optional[str] = None) -> Optional[str]:
        """
        ReportState에서 직접 PDF 생성
        
        Args:
            state: ReportState (final_report 필드 필요)
            filename: 출력 파일명
        
        Returns:
            생성된 PDF 파일 경로
        """
        report = state.get("final_report")
        if not report:
            print("❌ final_report가 없습니다.")
            return None
        
        target = state.get("target_companies", ["Unknown"])[0]
        title = f"{target} Investment Analysis"
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"report_{target}_{timestamp}.pdf"
        
        return self.export_to_pdf(report, filename, title)


# 편의 함수
def export_report(markdown_content: str, filename: str = None) -> Optional[str]:
    """간편 PDF 내보내기"""
    exporter = ReportExporter()
    return exporter.export_to_pdf(markdown_content, filename)
