from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging


class ConversionError(RuntimeError):
    """Raised when a conversion cannot be completed."""


@dataclass
class ConversionContext:
    work_dir: Path
    logger: logging.Logger


@dataclass
class BaseConverter:
    converter_id: str
    tool: str
    inputs: set[str]
    outputs: set[str]

    def can_convert(self, input_ext: str, output_ext: str) -> bool:
        return input_ext in self.inputs and output_ext in self.outputs

    def convert(self, source_path: Path, target_path: Path, context: ConversionContext) -> None:
        raise NotImplementedError
