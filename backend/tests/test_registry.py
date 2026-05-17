import logging

from app.converters.registry import ConverterRegistry
from app.utils import build_output_filename, is_private_address, normalize_extension, sanitize_filename


def test_normalize_extension_tar_gz() -> None:
    assert normalize_extension("archive.tar.gz") == "tar.gz"
    assert normalize_extension("report.PDF") == "pdf"


def test_build_output_filename() -> None:
    assert build_output_filename("report", "pdf") == "report.pdf"
    assert build_output_filename("archive", "tar.gz") == "archive.tar.gz"


def test_sanitize_filename() -> None:
    assert sanitize_filename("../weird name.txt") == "weird_name.txt"


def test_is_private_address() -> None:
    assert is_private_address("127.0.0.1")
    assert is_private_address("192.168.1.5")
    assert not is_private_address("8.8.8.8")


def test_supported_targets() -> None:
    registry = ConverterRegistry(logging.getLogger("test"))
    targets = registry.supported_targets("png")
    assert "jpg" in targets
