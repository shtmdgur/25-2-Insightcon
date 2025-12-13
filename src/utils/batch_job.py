"""
Gemini Batch API 통합

대량 KG 구축 작업을 Batch API로 처리하여 비용 50% 절감
"""
import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Gemini Client 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


class BatchJobStatus:
    """Batch Job 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BatchJobManager:
    """
    Gemini Batch API 작업 관리자
    
    대량 요청을 배치로 처리하여 비용 절감
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        output_dir: str = "./data/batch_jobs"
    ):
        """
        Args:
            model_name: 사용할 Gemini 모델
            output_dir: Batch Job 출력 디렉토리
        """
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_batch_request_file(
        self,
        requests: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Batch 요청 JSONL 파일 생성
        
        Args:
            requests: 요청 목록
            output_path: 출력 파일 경로 (기본: 자동 생성)
        
        Returns:
            생성된 파일 경로
        """
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.output_dir / f"batch_request_{timestamp}.jsonl"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for req in requests:
                f.write(json.dumps(req, ensure_ascii=False) + '\n')
        
        logger.info(f"Created batch request file: {output_path}")
        return str(output_path)
    
    def submit_batch_job(self, request_file_path: str) -> str:
        """
        Batch Job 제출
        
        Args:
            request_file_path: 요청 파일 경로
        
        Returns:
            Job ID
        """
        # Gemini Batch API 사용 (실제 API 구조는 확인 필요)
        # 현재는 Placeholder 구현
        logger.info(f"Submitting batch job: {request_file_path}")
        
        # TODO: 실제 Gemini Batch API 호출
        # job = genai.batch.create(...)
        # return job.id
        
        # Placeholder: 파일명 기반 임시 Job ID
        job_id = f"batch_{Path(request_file_path).stem}"
        return job_id
    
    def poll_batch_job(
        self,
        job_id: str,
        polling_interval: int = 10,
        max_attempts: int = 60
    ) -> Dict[str, Any]:
        """
        Batch Job 상태 폴링
        
        Args:
            job_id: Job ID
            polling_interval: 폴링 간격 (초)
            max_attempts: 최대 폴링 시도 횟수
        
        Returns:
            Job 상태 및 결과
        """
        logger.info(f"Polling batch job: {job_id}")
        
        for attempt in range(max_attempts):
            # TODO: 실제 Gemini Batch API 상태 조회
            # job_status = genai.batch.get(job_id)
            
            # Placeholder
            job_status = {
                "id": job_id,
                "status": BatchJobStatus.COMPLETED if attempt > 2 else BatchJobStatus.IN_PROGRESS,
                "results": []
            }
            
            if job_status["status"] == BatchJobStatus.COMPLETED:
                logger.info(f"Batch job completed: {job_id}")
                return job_status
            
            elif job_status["status"] == BatchJobStatus.FAILED:
                logger.error(f"Batch job failed: {job_id}")
                raise RuntimeError(f"Batch job failed: {job_id}")
            
            logger.info(f"Job {job_id} is {job_status['status']}. Retrying in {polling_interval}s...")
            time.sleep(polling_interval)
        
        raise TimeoutError(f"Batch job polling timeout: {job_id}")
    
    def run_batch_job(
        self,
        requests: List[Dict[str, Any]],
        wait_for_completion: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Batch Job 전체 실행 (생성 → 제출 → 폴링)
        
        Args:
            requests: 요청 목록
            wait_for_completion: 완료까지 대기 여부
        
        Returns:
            Job 결과 (wait_for_completion=False면 None)
        """
        # 1. JSONL 파일 생성
        request_file = self.create_batch_request_file(requests)
        
        # 2. Batch Job 제출
        job_id = self.submit_batch_job(request_file)
        
        # 3. 폴링 (옵션)
        if wait_for_completion:
            return self.poll_batch_job(job_id)
        else:
            return {"id": job_id, "status": "submitted"}


def create_kg_extraction_requests(
    documents: List[str],
    prompt_template: str
) -> List[Dict[str, Any]]:
    """
    KG 추출을 위한 Batch 요청 생성
    
    Args:
        documents: 문서 목록
        prompt_template: 프롬프트 템플릿
    
    Returns:
        Batch 요청 목록
    """
    requests = []
    
    for i, doc in enumerate(documents):
        request = {
            "custom_id": f"kg_extract_{i}",
            "method": "POST",
            "url": "/v1/generate",
            "body": {
                "model": "gemini-2.5-flash",
                "prompt": prompt_template.format(document=doc)
            }
        }
        requests.append(request)
    
    return requests
