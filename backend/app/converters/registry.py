from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import logging

from .base import ConversionContext, ConversionError
from .tools import (
    ArchiveConverter,
    EbookConverter,
    FfmpegConverter,
    ImageMagickConverter,
    LibreOfficeConverter,
    PandocConverter,
)
from ..formats import PIPELINES
from ..utils import build_output_filename, normalize_extension


@dataclass
class ConverterInfo:
    converter_id: str
    tool: str
    inputs: set[str]
    outputs: set[str]
    converter: object


class ConverterRegistry:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.converters = self._load_converters()

    def _load_converters(self) -> list[ConverterInfo]:
        converter_map = {
            "imagemagick": ImageMagickConverter,
            "ffmpeg": FfmpegConverter,
            "pandoc": PandocConverter,
            "libreoffice": LibreOfficeConverter,
            "ebook-convert": EbookConverter,
            "archive": ArchiveConverter,
        }
        converters: list[ConverterInfo] = []
        for pipeline in PIPELINES:
            converter_cls = converter_map.get(pipeline["tool"])
            if not converter_cls:
                continue
            inputs = set(pipeline["inputs"])
            outputs = set(pipeline["outputs"])
            converter = converter_cls(
                converter_id=pipeline["id"],
                tool=pipeline["tool"],
                inputs=inputs,
                outputs=outputs,
            )
            converters.append(
                ConverterInfo(
                    converter_id=pipeline["id"],
                    tool=pipeline["tool"],
                    inputs=inputs,
                    outputs=outputs,
                    converter=converter,
                )
            )
        return converters

    def supported_inputs(self) -> list[str]:
        formats = set()
        for converter in self.converters:
            formats.update(converter.inputs)
        return sorted(formats)

    def supported_targets(self, input_ext: str) -> list[str]:
        input_ext = normalize_extension(input_ext)
        targets = set()
        for converter in self.converters:
            if input_ext in converter.inputs:
                targets.update(converter.outputs)
        targets.discard(input_ext)
        return sorted(targets)

    def find_converter(self, input_ext: str, output_ext: str) -> ConverterInfo | None:
        input_ext = normalize_extension(input_ext)
        output_ext = normalize_extension(output_ext)
        for converter in self.converters:
            if input_ext in converter.inputs and output_ext in converter.outputs:
                return converter
        return None

    def convert_file(
        self,
        source_path: Path,
        output_ext: str,
        output_dir: Path,
    ) -> Path:
        input_ext = normalize_extension(source_path.name)
        output_ext = normalize_extension(output_ext)
        converter_info = self.find_converter(input_ext, output_ext)
        if not converter_info:
            raise ConversionError(f"Unsupported conversion: {input_ext} -> {output_ext}")
        output_filename = build_output_filename(source_path.stem, output_ext)
        target_path = output_dir / output_filename
        context = ConversionContext(work_dir=output_dir, logger=self.logger)
        converter_info.converter.convert(source_path, target_path, context)
        if not target_path.exists():
            raise ConversionError("Conversion did not produce an output file.")
        return target_path

    def supported_pairs(self) -> dict[str, list[str]]:
        pairs: dict[str, set[str]] = {}
        for converter in self.converters:
            for input_ext in converter.inputs:
                pairs.setdefault(input_ext, set()).update(converter.outputs)
        return {key: sorted(values) for key, values in pairs.items()}

    def ensure_supported(self, input_exts: Iterable[str], output_ext: str) -> None:
        output_ext = normalize_extension(output_ext)
        for input_ext in input_exts:
            input_ext = normalize_extension(input_ext)
            if input_ext == output_ext:
                raise ConversionError("Input and output formats are identical.")
            if not self.find_converter(input_ext, output_ext):
                raise ConversionError(f"Unsupported conversion: {input_ext} -> {output_ext}")
