"""Small standard-library PEP 517 backend for MaintainerGuard."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path


NAME = "maintainerguard"
VERSION = "0.1.0"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"
ROOT = Path(__file__).resolve().parent


def get_requires_for_build_wheel(config_settings=None):
    return []


def get_requires_for_build_sdist(config_settings=None):
    return []


def get_requires_for_build_editable(config_settings=None):
    return []


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    filename = f"{NAME}-{VERSION}-py3-none-any.whl"
    destination = Path(wheel_directory) / filename
    records: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _wheel_files():
            _write_wheel_file(archive, path.relative_to(ROOT).as_posix(), path.read_bytes(), records)
        metadata = _metadata().encode("utf-8")
        wheel = (
            "Wheel-Version: 1.0\n"
            "Generator: maintainerguard-build 0.1\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode("utf-8")
        _write_wheel_file(archive, f"{DIST_INFO}/METADATA", metadata, records)
        _write_wheel_file(archive, f"{DIST_INFO}/WHEEL", wheel, records)
        _write_wheel_file(archive, f"{DIST_INFO}/entry_points.txt", _entry_points(), records)
        _write_wheel_file(
            archive,
            f"{DIST_INFO}/licenses/LICENSE",
            (ROOT / "LICENSE").read_bytes(),
            records,
        )
        record_buffer = io.StringIO()
        writer = csv.writer(record_buffer, lineterminator="\n")
        writer.writerows(records)
        writer.writerow((f"{DIST_INFO}/RECORD", "", ""))
        archive.writestr(f"{DIST_INFO}/RECORD", record_buffer.getvalue().encode("utf-8"))
    return filename


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    filename = f"{NAME}-{VERSION}-py3-none-any.whl"
    destination = Path(wheel_directory) / filename
    records: list[tuple[str, str, str]] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        wheel = (
            "Wheel-Version: 1.0\n"
            "Generator: maintainerguard-build 0.1\n"
            "Root-Is-Purelib: true\n"
            "Tag: py3-none-any\n"
        ).encode("utf-8")
        _write_wheel_file(archive, "maintainerguard-editable.pth", f"{ROOT}\n".encode("utf-8"), records)
        _write_wheel_file(archive, f"{DIST_INFO}/METADATA", _metadata().encode("utf-8"), records)
        _write_wheel_file(archive, f"{DIST_INFO}/WHEEL", wheel, records)
        _write_wheel_file(archive, f"{DIST_INFO}/entry_points.txt", _entry_points(), records)
        _write_wheel_file(
            archive,
            f"{DIST_INFO}/licenses/LICENSE",
            (ROOT / "LICENSE").read_bytes(),
            records,
        )
        record_buffer = io.StringIO()
        writer = csv.writer(record_buffer, lineterminator="\n")
        writer.writerows(records)
        writer.writerow((f"{DIST_INFO}/RECORD", "", ""))
        archive.writestr(f"{DIST_INFO}/RECORD", record_buffer.getvalue().encode("utf-8"))
    return filename


def build_sdist(sdist_directory, config_settings=None):
    filename = f"{NAME}-{VERSION}.tar.gz"
    destination = Path(sdist_directory) / filename
    prefix = f"{NAME}-{VERSION}"
    with tarfile.open(destination, "w:gz") as archive:
        for path in _source_files():
            archive.add(path, arcname=f"{prefix}/{path.relative_to(ROOT)}")
        package_info = _metadata().encode("utf-8")
        info = tarfile.TarInfo(f"{prefix}/PKG-INFO")
        info.size = len(package_info)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(package_info))
    return filename


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    return prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    directory = Path(metadata_directory) / DIST_INFO
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "METADATA").write_text(_metadata(), encoding="utf-8")
    (directory / "WHEEL").write_text(
        "Wheel-Version: 1.0\nGenerator: maintainerguard-build 0.1\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        encoding="utf-8",
    )
    return DIST_INFO


def _write_wheel_file(archive, name: str, data: bytes, records) -> None:
    archive.writestr(name, data)
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode("ascii")
    records.append((name, f"sha256={digest}", str(len(data))))


def _entry_points() -> bytes:
    return (
        b"[console_scripts]\n"
        b"maintainerguard = maintainerguard.cli:main\n"
        b"mg = maintainerguard.cli:main\n"
    )


def _source_files():
    excluded_parts = {".git", "__pycache__", "dist", "build", ".venv"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in excluded_parts for part in path.parts):
            continue
        if path.name == ".DS_Store" or path.suffix in {".pyc", ".whl", ".gz", ".zip"}:
            continue
        yield path


def _wheel_files():
    for path in sorted((ROOT / NAME).glob("*.py")):
        yield path
    for relative in ("action.yml", ".maintainerguard.toml"):
        path = ROOT / relative
        if path.exists():
            yield path
    for base in ("examples/sample-data", "schemas"):
        root = ROOT / base
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != ".DS_Store" and path.suffix != ".pyc":
                yield path


def _metadata() -> str:
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {NAME}\n"
        f"Version: {VERSION}\n"
        "Summary: Evidence-first AI maintainer assistant for merge, security, and release readiness.\n"
        "Requires-Python: >=3.11\n"
        "License: Apache-2.0\n"
        "License-File: LICENSE\n"
        "Keywords: maintainers,github-actions,security,release,scanner,oss\n"
        "Classifier: Development Status :: 3 - Alpha\n"
        "Classifier: Environment :: Console\n"
        "Classifier: Intended Audience :: Developers\n"
        "Classifier: License :: OSI Approved :: Apache Software License\n"
        "Classifier: Operating System :: OS Independent\n"
        "Classifier: Programming Language :: Python :: 3\n"
        "Classifier: Programming Language :: Python :: 3.11\n"
        "Classifier: Topic :: Software Development :: Quality Assurance\n"
    )
