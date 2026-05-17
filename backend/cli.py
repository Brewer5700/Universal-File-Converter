from __future__ import annotations

import argparse
from pathlib import Path
import logging
import sys

from app.converters.base import ConversionError
from app.converters.registry import ConverterRegistry
from app.utils import normalize_extension, ensure_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Universal File Converter CLI")
    parser.add_argument("inputs", nargs="+", help="Input file paths")
    parser.add_argument("-t", "--target", required=True, help="Target output format")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = logging.getLogger("universal_converter.cli")
    logging.basicConfig(level="INFO")
    registry = ConverterRegistry(logger)

    output_dir = ensure_directory(Path(args.output_dir))
    input_paths = [Path(path).expanduser().resolve() for path in args.inputs]
    missing = [str(path) for path in input_paths if not path.exists()]
    if missing:
        logger.error("Missing input files: %s", ", ".join(missing))
        return 1

    input_exts = [normalize_extension(path.name) for path in input_paths]
    target = normalize_extension(args.target)

    try:
        registry.ensure_supported(input_exts, target)
    except ConversionError as exc:
        logger.error(str(exc))
        return 1

    for path in input_paths:
        try:
            output_path = registry.convert_file(path, target, output_dir)
        except ConversionError as exc:
            logger.error("Failed to convert %s: %s", path.name, exc)
            return 1
        logger.info("Converted %s -> %s", path.name, output_path.name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
