from __future__ import annotations

from pathlib import Path
import logging
import uuid

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .converters.base import ConversionError
from .converters.registry import ConverterRegistry
from .formats import FORMATS, PIPELINES
from .jobs import JobManager
from .storage import init_storage, job_output_dir, job_upload_dir, save_upload_file
from .utils import is_private_address, normalize_extension


logger = logging.getLogger("universal_converter")
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="Universal File Converter", version="0.1.0")

registry = ConverterRegistry(logger)
job_manager = JobManager(registry, logger)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_storage()


async def verify_access(
    request: Request,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    if not settings.allow_public and not is_private_address(request.client.host):
        raise HTTPException(status_code=403, detail="Public access is disabled.")


@app.get("/api/health", dependencies=[Depends(verify_access)])
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/formats", dependencies=[Depends(verify_access)])
def list_formats() -> dict:
    return {
        "formats": FORMATS,
        "pipelines": PIPELINES,
        "supported_inputs": registry.supported_inputs(),
        "supported_targets": registry.supported_pairs(),
    }


@app.get("/api/conversions", dependencies=[Depends(verify_access)])
def list_conversions(input_ext: str) -> dict:
    targets = registry.supported_targets(input_ext)
    if not targets:
        raise HTTPException(status_code=404, detail="No conversions available for input.")
    return {"input": normalize_extension(input_ext), "targets": targets}


@app.post("/api/jobs", dependencies=[Depends(verify_access)])
async def create_job(
    request: Request,
    target_format: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    target_format = normalize_extension(target_format)
    if not target_format:
        raise HTTPException(status_code=400, detail="Target format is required.")

    input_extensions = []
    for upload in files:
        input_ext = normalize_extension(upload.filename or "")
        if not input_ext:
            raise HTTPException(status_code=400, detail="Missing file extension.")
        input_extensions.append(input_ext)

    try:
        registry.ensure_supported(input_extensions, target_format)
    except ConversionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = uuid.uuid4().hex
    upload_dir = job_upload_dir(job_id)
    saved_paths: list[Path] = []

    for upload in files:
        try:
            saved_path = save_upload_file(
                upload.file,
                upload.filename or "file",
                upload_dir,
                settings.max_upload_bytes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        finally:
            await upload.close()
        saved_paths.append(saved_path)

    job = job_manager.create_job(saved_paths, target_format, job_id=job_id)
    return {"job": job.to_dict(base_url=str(request.base_url))}


@app.get("/api/jobs/{job_id}", dependencies=[Depends(verify_access)])
def get_job(job_id: str, request: Request) -> dict:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    base_url = str(request.base_url)
    return {"job": job.to_dict(base_url=base_url)}


@app.get("/api/jobs/{job_id}/download", dependencies=[Depends(verify_access)])
def download(job_id: str, file: str | None = None) -> FileResponse:
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job is not completed.")
    if not job.outputs:
        raise HTTPException(status_code=404, detail="No output files found.")
    if file:
        for output in job.outputs:
            if output.filename == file:
                return FileResponse(output.path, filename=output.filename)
        raise HTTPException(status_code=404, detail="Requested file not found.")
    if len(job.outputs) > 1:
        raise HTTPException(status_code=400, detail="Multiple outputs available, specify file.")
    output = job.outputs[0]
    return FileResponse(output.path, filename=output.filename)


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
