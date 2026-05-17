from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
import re


ARCHIVE_EXTENSIONS = (".tar.gz",)


def normalize_extension(name: str) -> str:
    lowered = name.lower().strip()
    for archive_ext in ARCHIVE_EXTENSIONS:
        if lowered.endswith(archive_ext):
            return archive_ext.lstrip(".")
    if "." not in lowered:
        return lowered
    return lowered.rsplit(".", 1)[-1]


def build_output_filename(stem: str, output_ext: str) -> str:
    output_ext = output_ext.lower().lstrip(".")
    if output_ext == "tar.gz":
        return f"{stem}.tar.gz"
    return f"{stem}.{output_ext}"


def sanitize_filename(filename: str) -> str:
    filename = filename.strip().replace("\\", "/")
    filename = filename.split("/")[-1]
    filename = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return filename or "file"


def is_private_address(host: str | None) -> bool:
    if not host:
        return True
    if host in {"localhost", "127.0.0.1"}:
        return True
    try:
        addr = ip_address(host)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
