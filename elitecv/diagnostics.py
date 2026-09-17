from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess


_COMMAND_TIMEOUT_SECONDS = 10
_TEMPLATE_FILES = (
    Path(__file__).resolve().parents[1] / "templates" / "default" / "resume.tex",
    Path(__file__).resolve().parent / "template.tex",
)
_PACKAGE_PATTERN = re.compile(r"\\usepackage(?:\[[^]]*\])?\{([^}]+)\}")
_CLASS_PATTERN = re.compile(r"\\documentclass(?:\[[^]]*\])?\{([^}]+)\}")


@dataclass(frozen=True)
class Dependency:
    check_id: str
    label: str
    lookup: str
    category: str
    required: bool
    remediation: str
    kind: str


@dataclass(frozen=True)
class DependencyCheck:
    check_id: str
    status: str
    category: str
    remediation: str
    required: bool


def _template_dependencies() -> tuple[str, ...]:
    filenames: set[str] = set()
    for template_path in _TEMPLATE_FILES:
        text = template_path.read_text(encoding="utf-8")
        filenames.update(f"{name}.sty" for name in _PACKAGE_PATTERN.findall(text))
        filenames.update(f"{name}.cls" for name in _CLASS_PATTERN.findall(text))
    return tuple(sorted(filenames))


def dependency_inventory() -> tuple[Dependency, ...]:
    dependencies = [
        Dependency(
            "renderer.tool.pdflatex",
            "pdflatex",
            "pdflatex",
            "renderer-tool",
            True,
            "Install TeX Live or MiKTeX with pdflatex.",
            "command",
        ),
        Dependency(
            "renderer.tool.pdftotext",
            "pdftotext",
            "pdftotext",
            "pdf-inspection",
            True,
            "Install Poppler utilities with pdftotext.",
            "command",
        ),
        Dependency(
            "renderer.tool.pdftoppm",
            "pdftoppm",
            "pdftoppm",
            "pdf-inspection",
            True,
            "Install Poppler utilities with pdftoppm.",
            "command",
        ),
        Dependency(
            "renderer.tool.pdfinfo",
            "pdfinfo",
            "pdfinfo",
            "pdf-inspection",
            True,
            "Install Poppler utilities with pdfinfo.",
            "command",
        ),
        Dependency(
            "renderer.tool.kpsewhich",
            "kpsewhich",
            "kpsewhich",
            "tex-resolution",
            True,
            "Install TeX Live or MiKTeX with kpsewhich.",
            "command",
        ),
        Dependency(
            "renderer.tool.latexmk",
            "latexmk (optional)",
            "latexmk",
            "renderer-tool",
            False,
            "Install latexmk for the optional wrapper; build falls back to pdflatex.",
            "command",
        ),
    ]
    for filename in _template_dependencies():
        dependencies.append(
            Dependency(
                f"tex.file.{filename}",
                filename,
                filename,
                "tex-package",
                True,
                f"Install the TeX package providing {filename}.",
                "tex-file",
            )
        )
    return tuple(dependencies)


def _check_command(dependency: Dependency) -> bool:
    return shutil.which(dependency.lookup) is not None


def _check_tex_file(dependency: Dependency) -> bool:
    if shutil.which("kpsewhich") is None:
        return False
    try:
        result = subprocess.run(
            ["kpsewhich", dependency.lookup],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def check_dependencies() -> list[DependencyCheck]:
    checks: list[DependencyCheck] = []
    for dependency in dependency_inventory():
        available = (
            _check_command(dependency)
            if dependency.kind == "command"
            else _check_tex_file(dependency)
        )
        status = "pass" if available else ("missing" if dependency.required else "optional-missing")
        checks.append(
            DependencyCheck(
                check_id=dependency.check_id,
                status=status,
                category=dependency.category,
                remediation=dependency.remediation,
                required=dependency.required,
            )
        )
    return checks


def required_dependency_failures(checks: list[DependencyCheck]) -> list[DependencyCheck]:
    return [check for check in checks if check.required and check.status != "pass"]


def dependency_check_json(check: DependencyCheck) -> dict[str, object]:
    payload = asdict(check)
    payload.pop("required")
    payload["requirement"] = "required" if check.required else "optional"
    return payload


def runtime_dependency_available() -> bool:
    return importlib.util.find_spec("yaml") is not None
