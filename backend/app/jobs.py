from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable
import logging
import uuid
import shutil

from .config import settings
from .converters.base import ConversionError
from .converters.registry import ConverterRegistry
from .storage import job_output_dir, job_work_dir


class JobStatus:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobOutput:
    filename: str
    path: Path


@dataclass
class Job:
    job_id: str
    input_files: list[str]
    target_format: str
    status: str = JobStatus.QUEUED
    progress: int = 0
    outputs: list[JobOutput] = field(default_factory=list)
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self, base_url: str | None = None) -> dict:
        outputs = []
        for output in self.outputs:
            download_url = None
            if base_url:
                download_url = f"{base_url}api/jobs/{self.job_id}/download?file={output.filename}"
            outputs.append({"filename": output.filename, "download_url": download_url})
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "target_format": self.target_format,
            "input_files": self.input_files,
            "outputs": outputs,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class JobStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, Job] = {}

    def add(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.job_id] = job


class JobManager:
    def __init__(self, registry: ConverterRegistry, logger: logging.Logger) -> None:
        self.registry = registry
        self.logger = logger
        self.store = JobStore()
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)

    def create_job(
        self,
        input_paths: Iterable[Path],
        target_format: str,
        job_id: str | None = None,
    ) -> Job:
        job_id = job_id or uuid.uuid4().hex
        job = Job(
            job_id=job_id,
            input_files=[path.name for path in input_paths],
            target_format=target_format,
        )
        self.store.add(job)
        self.executor.submit(self._run_job, job, list(input_paths))
        return job

    def _run_job(self, job: Job, input_paths: list[Path]) -> None:
        job.status = JobStatus.RUNNING
        job.progress = 5
        job.updated_at = datetime.now(timezone.utc)
        self.store.update(job)
        output_dir = job_output_dir(job.job_id)
        work_dir = job_work_dir(job.job_id)
        total = len(input_paths)
        try:
            for index, path in enumerate(input_paths, start=1):
                job.progress = int(5 + (index - 1) / total * 80)
                job.updated_at = datetime.now(timezone.utc)
                self.store.update(job)
                output_path = self.registry.convert_file(path, job.target_format, output_dir)
                job.outputs.append(JobOutput(filename=output_path.name, path=output_path))
                job.progress = int(5 + index / total * 80)
                job.updated_at = datetime.now(timezone.utc)
                self.store.update(job)
        except ConversionError as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.progress = 100
            job.updated_at = datetime.now(timezone.utc)
            self.store.update(job)
            self.logger.error("Job %s failed: %s", job.job_id, exc)
            return
        finally:
            if work_dir.exists():
                shutil.rmtree(work_dir, ignore_errors=True)

        job.status = JobStatus.COMPLETED
        job.progress = 100
        job.updated_at = datetime.now(timezone.utc)
        self.store.update(job)

    def get_job(self, job_id: str) -> Job | None:
        return self.store.get(job_id)
