from __future__ import annotations

from pathlib import Path
import shutil
from typing import IO

from .config import settings
from .utils import ensure_directory, sanitize_filename


UPLOADS_DIR = settings.data_dir / "uploads"
OUTPUTS_DIR = settings.data_dir / "outputs"
WORK_DIR = settings.data_dir / "work"


def init_storage() -> None:
    ensure_directory(settings.data_dir)
    ensure_directory(UPLOADS_DIR)
    ensure_directory(OUTPUTS_DIR)
    ensure_directory(WORK_DIR)


def job_upload_dir(job_id: str) -> Path:
    return ensure_directory(UPLOADS_DIR / job_id)


def job_output_dir(job_id: str) -> Path:
    return ensure_directory(OUTPUTS_DIR / job_id)


def job_work_dir(job_id: str) -> Path:
    return ensure_directory(WORK_DIR / job_id)


def save_upload_file(
    file_obj: IO[bytes],
    filename: str,
    destination_dir: Path,
    max_bytes: int,
) -> Path:
    filename = sanitize_filename(filename)
    destination = destination_dir / filename
    size = 0
    with destination.open("wb") as dest:
        while True:
            chunk = file_obj.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                dest.close()
                destination.unlink(missing_ok=True)
                raise ValueError("File exceeds maximum allowed size.")
            dest.write(chunk)
    return destination


def copy_to_job_dir(source_path: Path, destination_dir: Path) -> Path:
    destination = destination_dir / sanitize_filename(source_path.name)
    shutil.copy2(source_path, destination)
    return destination
