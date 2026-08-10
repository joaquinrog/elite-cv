from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess


@dataclass(frozen=True)
class SafetyFinding:
    code: str
    path: str
    message: str


TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".py",
    ".tex",
    ".sh",
    ".ps1",
    ".html",
    ".htm",
    ".xml",
    ".ini",
    ".cfg",
    ".csv",
}
FORBIDDEN_PARTS = {"workspace", "dist"}
LOCAL_ONLY_ROOTS = {"data", "sources", "workspace", "dist"}
LOCAL_ARTIFACT_PARTS = {"__pycache__", ".pytest_cache", ".venv", "venv", "build"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAWS_SECRET_ACCESS_KEY\s*="),
    re.compile(
        r"\b(?:api[_-]?key|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b"
    ),
)
PRIVATE_EMAIL_RE = re.compile(r"\b[\w.+-]+@(?!example\.com\b|localhost\b)[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(?<![\d-])(?:\+\d{1,3}[ .-]?)?(?:(?:\(\d{2,4}\)[ .-]?\d{3}[ .-]\d{4})|(?:\d{3}[ .-]\d{3}[ .-]\d{4}))(?![\d-])"
)
SKIP_CONTENT_SCAN_PARTS = {"tests"}
PUBLIC_SAMPLE_BINARY_RE = re.compile(
    r"^examples/synthetic-profile/outputs/(?:robotics-software|ai-internship)/share/(?:cv\.pdf|preview\.png)$"
)


def _is_text(path: Path) -> bool:
    return (
        path.suffix.lower() in TEXT_SUFFIXES
        or path.name in {".gitignore", "AGENTS.md", "LICENSE"}
        or path.name.endswith(".env")
    )


def _is_local_artifact(parts: tuple[str, ...]) -> bool:
    return any(part in LOCAL_ARTIFACT_PARTS or part.endswith(".egg-info") for part in parts)


def _is_forbidden_path(parts: tuple[str, ...], path: Path) -> bool:
    has_private_source_path = any(
        parts[index : index + 2] == ("sources", "private")
        for index in range(len(parts) - 1)
    )
    return (
        (bool(parts) and parts[0] in LOCAL_ONLY_ROOTS)
        or has_private_source_path
        or any(part in FORBIDDEN_PARTS for part in parts)
        or path.name == ".env"
        or path.name.startswith(".env.")
    )


def _scan_text(path: str, text: str, findings: list[SafetyFinding]) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(SafetyFinding("secret_pattern", path, "secret-like pattern detected"))
            break
    if PRIVATE_EMAIL_RE.search(text):
        findings.append(SafetyFinding("private_email", path, "non-example email detected"))
    if PHONE_RE.search(text) and "schema_version" not in text:
        findings.append(SafetyFinding("phone_pattern", path, "phone-like pattern detected"))


def _scan_pdf(path: Path, relative: str, findings: list[SafetyFinding]) -> None:
    for command in (("pdftotext", "-layout", str(path), "-"), ("pdfinfo", str(path))):
        if not shutil.which(command[0]):
            findings.append(
                SafetyFinding("unscannable_pdf", relative, f"missing required tool `{command[0]}`")
            )
            return
        try:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            findings.append(SafetyFinding("unscannable_pdf", relative, "could not inspect PDF text and metadata"))
            return
        _scan_text(relative, result.stdout or "", findings)


def scan_public_tree(root: Path) -> list[SafetyFinding]:
    findings: list[SafetyFinding] = []
    root = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        if parts and parts[0] == ".git":
            continue
        if _is_forbidden_path(parts, path):
            findings.append(SafetyFinding("forbidden_path", relative, "local-only path is present"))
        if _is_local_artifact(parts):
            continue
        if path.suffix.lower() in {".pem", ".key"} or path.name in {"credentials.json", "auth.json"}:
            findings.append(SafetyFinding("forbidden_path", relative, "credential-like file is present"))
        if not _is_text(path):
            if not PUBLIC_SAMPLE_BINARY_RE.fullmatch(relative):
                findings.append(SafetyFinding("unexpected_binary", relative, "binary artifact is not allowlisted"))
            elif path.suffix.lower() == ".pdf":
                _scan_pdf(path, relative, findings)
            continue
        if any(part in SKIP_CONTENT_SCAN_PARTS for part in parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        _scan_text(relative, text, findings)
    return findings
