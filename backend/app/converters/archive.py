from __future__ import annotations

from pathlib import Path
import shutil
import tarfile
import zipfile

from .base import ConversionError


def _unpack_archive(source_path: Path, extract_dir: Path) -> None:
    if source_path.suffix == ".zip":
        with zipfile.ZipFile(source_path, "r") as archive:
            archive.extractall(extract_dir)
        return
    if source_path.suffix == ".tar" or source_path.name.endswith(".tar.gz"):
        with tarfile.open(source_path, "r:*") as archive:
            archive.extractall(extract_dir)
        return
    raise ConversionError(f"Unsupported archive format: {source_path.name}")


def _pack_archive(source_dir: Path, target_path: Path) -> None:
    if target_path.suffix == ".zip":
        with zipfile.ZipFile(target_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(source_dir))
        return
    if target_path.suffix == ".tar" or target_path.name.endswith(".tar.gz"):
        mode = "w:gz" if target_path.name.endswith(".tar.gz") else "w"
        with tarfile.open(target_path, mode) as archive:
            archive.add(source_dir, arcname=".")
        return
    raise ConversionError(f"Unsupported archive format: {target_path.name}")


def convert_archive(source_path: Path, target_path: Path, work_dir: Path) -> None:
    if source_path.resolve() == target_path.resolve():
        raise ConversionError("Source and target archive are identical.")
    extract_dir = work_dir / "extract"
    extract_dir.mkdir(parents=True, exist_ok=True)
    _unpack_archive(source_path, extract_dir)
    _pack_archive(extract_dir, target_path)
