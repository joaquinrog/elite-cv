from pathlib import Path
import os
import stat
import subprocess

import pytest

from elitecv.cli import _doctor, _init, main
from elitecv.models import WorkspaceError, load_workspace


def test_init_records_local_privacy_defaults(tmp_path):
    assert _init(tmp_path, "Robotics Software Intern", "letter") == 0

    policy = (tmp_path / "workspace" / "policy.yml").read_text(encoding="utf-8")
    ignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "track_structured_profile: false" in policy
    assert "remote_artifacts: false" in policy
    assert "data/*.yml" in ignore
    assert "sources/private/**" in ignore


def test_init_opt_in_removes_structured_data_from_local_ignore_block(tmp_path):
    _init(tmp_path, "General", "letter")

    _init(tmp_path, "General", "letter", track_structured_profile=True)

    ignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "data/*.yml" not in ignore
    assert "sources/private/**" in ignore


def test_variant_create_rejects_a_path_traversal_id(tmp_path):
    _init(tmp_path, "General", "letter")
    template = tmp_path / "data" / "variants" / "robotics-software.yml"
    template.write_text(
        "schema_version: 1\nid: robotics-software\ntarget_role: General\n"
        "locale: en-US\npage_size: letter\npage_target: 1\nsections: []\n"
        "include_entries: []\nexclude_entries: []\nrequired_claim_ids: []\n"
        "allowed_disclosures: [shareable]\n",
        encoding="utf-8",
    )

    result = main(["variant", "create", "../escaped", "--root", str(tmp_path)])

    assert result == 1
    assert not (tmp_path / "data" / "escaped.yml").exists()


def test_workspace_loader_rejects_a_path_traversal_target():
    sample_root = Path(__file__).parents[2] / "examples" / "synthetic-profile"

    with pytest.raises(WorkspaceError, match="variant id"):
        load_workspace(sample_root, "../profile")


def test_init_hides_personal_workspace_files_in_a_git_repository(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True, text=True)
    _init(tmp_path, "General", "letter")
    (tmp_path / "sources" / "private" / "resume.txt").write_text("private\n", encoding="utf-8")
    share = tmp_path / "dist" / "general" / "share"
    share.mkdir(parents=True)
    (share / "cv.pdf").write_bytes(b"private")

    for path in ("data/profile.yml", "sources/private/resume.txt", "workspace/policy.yml", "dist/general/share/cv.pdf"):
        result = subprocess.run(
            ["git", "-C", str(tmp_path), "check-ignore", "-q", path],
            check=False,
        )
        assert result.returncode == 0

    status = subprocess.run(
        ["git", "-C", str(tmp_path), "status", "--short", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert status.stdout == ""


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits are unavailable")
def test_init_uses_owner_only_permissions_for_private_workspace_files(tmp_path):
    _init(tmp_path, "General", "letter")

    private_directories = (
        "data",
        "data/variants",
        "sources/private",
        "workspace",
        "workspace/review",
        "dist",
    )
    private_files = (
        "data/sources.yml",
        "data/claims.yml",
        "data/profile.yml",
        "data/variants/general.yml",
        "workspace/policy.yml",
        "workspace/review/open-questions.md",
    )
    for relative in private_directories:
        assert stat.S_IMODE((tmp_path / relative).stat().st_mode) == 0o700
    for relative in private_files:
        assert stat.S_IMODE((tmp_path / relative).stat().st_mode) == 0o600


def test_doctor_reports_a_timed_out_latex_lookup(monkeypatch, tmp_path):
    monkeypatch.setattr("elitecv.cli.shutil.which", lambda _tool: "/usr/bin/tool")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("kpsewhich", 10)

    monkeypatch.setattr("elitecv.cli.subprocess.run", timeout)

    assert _doctor(tmp_path) == 1
