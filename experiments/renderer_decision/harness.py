from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Callable

from elitecv.pdf_audit import audit_pdf_text


def redact_error(message: str, work_dir: Path | None = None) -> str:
    safe = str(message).replace("\\", "/")
    if work_dir:
        safe = safe.replace(str(work_dir).replace("\\", "/"), "<workdir>")
    safe = re.sub(r"/(?:[^\s/]+/)*[^\s/]+", "<path>", safe)
    safe = " ".join(safe.split())
    return safe[:997] + "..." if len(safe) > 1000 else safe


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class CommandAdapter:
    name: str
    command: tuple[str, ...]
    source_name: str = "cv.tex"
    version_args: tuple[str, ...] = ("--version",)
    build_command: Callable[[Path, Path], list[str]] | None = None

    def availability(self) -> dict[str, Any]:
        executable = self.command[0]
        if not shutil.which(executable):
            return {"available": False, "version": None, "error": "missing_tool"}
        try:
            result = subprocess.run(
                [executable, *self.version_args],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {"available": False, "version": None, "error": redact_error(str(exc))}
        first = (result.stdout or "").splitlines()
        return {"available": result.returncode == 0, "version": first[0][:160] if first else "unknown", "error": None}

    def build(self, source_dir: Path, output_dir: Path) -> dict[str, Any]:
        if not self.availability()["available"]:
            return {"status": "blocked", "error": "missing_tool"}
        output_dir.mkdir(parents=True, exist_ok=True)
        command = self.build_command(source_dir, output_dir) if self.build_command else [*self.command, str(source_dir / self.source_name)]
        try:
            subprocess.run(command, cwd=output_dir, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        except (OSError, subprocess.SubprocessError) as exc:
            return {"status": "error", "error": redact_error(str(exc), output_dir)}
        pdf = output_dir / "cv.pdf"
        return {"status": "pass" if pdf.is_file() else "error", "pdf_path": pdf, "error": None if pdf.is_file() else "missing_pdf"}


def measure_run(
    *, candidate: str, fixture: str, output_dir: Path, pdf_path: Path, preview_path: Path,
    text_path: Path, expected_text: list[str], target_role: str, page_count: int | None,
    elapsed_seconds: float, links: list[str], annotation_urls: set[str] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.is_file() else ""
    quality = audit_pdf_text(text, expected_fields={str(index): value for index, value in enumerate(expected_text)})
    sizes = {path.name: path.stat().st_size for path in (pdf_path, preview_path, text_path) if path.is_file()}
    return {
        "candidate": candidate,
        "fixture": fixture,
        "status": "blocked" if error == "missing_tool" else ("error" if error else "pass"),
        "elapsed_seconds": round(elapsed_seconds, 4),
        "artifact_sizes_bytes": sizes,
        "page_count": page_count,
        "text_quality": quality,
        "expected_text": expected_text,
        "target_role_absent": target_role.casefold() not in text.casefold(),
        "links": [
            {
                "url": url,
                "status": (
                    "found"
                    if annotation_urls is not None and url in annotation_urls
                    else "missing"
                    if annotation_urls is not None
                    else "not_measured"
                ),
            }
            for url in links
        ],
        "preview": {"available": preview_path.is_file(), "size_bytes": preview_path.stat().st_size if preview_path.is_file() else 0},
        "paths": {"pdf": pdf_path.name, "preview": preview_path.name, "text": text_path.name},
        "error": redact_error(error, output_dir) if error else None,
    }


def summarize_repeatability(first: dict[str, str], second: dict[str, str]) -> dict[str, bool]:
    keys = ("pdf_sha256", "preview_sha256")
    comparable = all(key in first and key in second for key in keys)
    return {"comparable": comparable, "identical": comparable and all(first[key] == second[key] for key in keys)}


def hashes_for_run(pdf_path: Path, preview_path: Path) -> dict[str, str]:
    return {"pdf_sha256": _sha256(pdf_path), "preview_sha256": _sha256(preview_path)}


def pdf_annotation_urls(pdf_path: Path) -> set[str]:
    result = subprocess.run(
        ["pdfinfo", "-url", str(pdf_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )
    return {
        match.group(1)
        for line in result.stdout.splitlines()
        if (match := re.search(r"(?:Annotation\s+)(\S+)$", line))
    }


def run_command_adapter(adapter: CommandAdapter, source_dir: Path, output_dir: Path, *, fixture: str, expected_text: list[str], target_role: str, links: list[str]) -> dict[str, Any]:
    start = time.monotonic()
    result = adapter.build(source_dir, output_dir)
    elapsed = time.monotonic() - start
    pdf = result.get("pdf_path", output_dir / "cv.pdf")
    text_path = output_dir / "cv.txt"
    preview_path = output_dir / "preview.png"
    if result["status"] == "pass":
        subprocess.run(["pdftotext", "-layout", str(pdf), str(text_path)], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-r", "100", str(pdf), str(output_dir / "preview")], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        preview_path = output_dir / "preview.png"
        page_count = _pdf_page_count(pdf)
    else:
        page_count = None
    annotation_urls = pdf_annotation_urls(pdf) if result["status"] == "pass" else None
    return measure_run(candidate=adapter.name, fixture=fixture, output_dir=output_dir, pdf_path=pdf, preview_path=preview_path, text_path=text_path, expected_text=expected_text, target_role=target_role, page_count=page_count, elapsed_seconds=elapsed, links=links, annotation_urls=annotation_urls, error=result.get("error"))


def _pdf_page_count(pdf_path: Path) -> int:
    result = subprocess.run(["pdfinfo", str(pdf_path)], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise ValueError("missing_page_count")
