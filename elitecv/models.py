from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


class WorkspaceError(RuntimeError):
    """Raised when a workspace cannot be loaded safely."""


VARIANT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def validate_variant_id(value: str) -> str:
    if not isinstance(value, str) or not VARIANT_ID_RE.fullmatch(value):
        raise WorkspaceError(
            "variant id must use lowercase letters, numbers, and hyphens only"
        )
    return value


@dataclass(frozen=True)
class WorkspaceDocuments:
    root: Path
    data_dir: Path
    sources: dict[str, Any]
    claims: dict[str, Any]
    profile: dict[str, Any]
    variant: dict[str, Any]
    variant_path: Path


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - doctor owns this path
        raise WorkspaceError(
            "PyYAML is missing. Install the package with `python -m pip install -e .`."
        ) from exc

    if not path.is_file():
        raise WorkspaceError(f"Missing structured file: {path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise WorkspaceError(f"Could not parse YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkspaceError(f"Structured file must contain a mapping: {path}")
    return value


def data_directory(root: Path) -> Path:
    data_dir = root / "data"
    if not data_dir.is_dir():
        raise WorkspaceError(
            f"Missing data directory: {data_dir}. Run `elitecv init` or pass a workspace root."
        )
    return data_dir


def load_workspace(root: Path, target: str) -> WorkspaceDocuments:
    root = root.resolve()
    target = validate_variant_id(target)
    data_dir = data_directory(root)
    variants_dir = data_dir / "variants"
    variant_path = (variants_dir / f"{target}.yml").resolve()
    try:
        variant_path.relative_to(variants_dir.resolve())
    except ValueError as exc:
        raise WorkspaceError(f"variant id resolves outside {variants_dir}") from exc
    if not variant_path.is_file():
        available = sorted(path.stem for path in variants_dir.glob("*.yml"))
        suffix = f" Available variants: {', '.join(available)}." if available else ""
        raise WorkspaceError(f"Missing variant `{target}` at {variant_path}.{suffix}")

    return WorkspaceDocuments(
        root=root,
        data_dir=data_dir,
        sources=load_yaml(data_dir / "sources.yml"),
        claims=load_yaml(data_dir / "claims.yml"),
        profile=load_yaml(data_dir / "profile.yml"),
        variant=load_yaml(variant_path),
        variant_path=variant_path,
    )
