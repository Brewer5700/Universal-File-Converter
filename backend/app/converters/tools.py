from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .archive import convert_archive
from .base import BaseConverter, ConversionContext, ConversionError


@dataclass
class CommandConverter(BaseConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        raise NotImplementedError

    def convert(self, source_path: Path, target_path: Path, context: ConversionContext) -> None:
        command = self.build_command(source_path, target_path)
        context.logger.info("Running conversion command: %s", " ".join(command))
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ConversionError(
                f"Conversion failed with {self.tool}: {result.stderr.strip() or result.stdout.strip()}"
            )


@dataclass
class ImageMagickConverter(CommandConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        binary = shutil.which("magick") or shutil.which("convert")
        if not binary:
            raise ConversionError("ImageMagick not found (magick/convert).")
        return [binary, str(source_path), str(target_path)]


@dataclass
class FfmpegConverter(CommandConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        binary = shutil.which("ffmpeg")
        if not binary:
            raise ConversionError("ffmpeg not found.")
        return [binary, "-y", "-i", str(source_path), str(target_path)]


@dataclass
class PandocConverter(CommandConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        binary = shutil.which("pandoc")
        if not binary:
            raise ConversionError("Pandoc not found.")
        return [binary, str(source_path), "-o", str(target_path)]


@dataclass
class LibreOfficeConverter(CommandConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        binary = shutil.which("libreoffice") or shutil.which("soffice")
        if not binary:
            raise ConversionError("LibreOffice not found (libreoffice/soffice).")
        output_ext = target_path.suffix.lstrip(".")
        if target_path.name.endswith(".tar.gz"):
            output_ext = "tar.gz"
        return [
            binary,
            "--headless",
            "--convert-to",
            output_ext,
            "--outdir",
            str(target_path.parent),
            str(source_path),
        ]

    def convert(self, source_path: Path, target_path: Path, context: ConversionContext) -> None:
        command = self.build_command(source_path, target_path)
        context.logger.info("Running conversion command: %s", " ".join(command))
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ConversionError(
                f"Conversion failed with {self.tool}: {result.stderr.strip() or result.stdout.strip()}"
            )
        produced = target_path.parent / f"{source_path.stem}.{target_path.suffix.lstrip('.')}"
        if target_path.name.endswith(".tar.gz"):
            produced = target_path.parent / f"{source_path.stem}.tar.gz"
        if produced != target_path:
            if not produced.exists():
                raise ConversionError("LibreOffice did not produce output file.")
            produced.replace(target_path)


@dataclass
class EbookConverter(CommandConverter):
    def build_command(self, source_path: Path, target_path: Path) -> list[str]:
        binary = shutil.which("ebook-convert")
        if not binary:
            raise ConversionError("Calibre ebook-convert not found.")
        return [binary, str(source_path), str(target_path)]


@dataclass
class ArchiveConverter(BaseConverter):
    def convert(self, source_path: Path, target_path: Path, context: ConversionContext) -> None:
        convert_archive(source_path, target_path, context.work_dir)
