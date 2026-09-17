from __future__ import annotations

import json

import pytest

from elitecv.approval import approve_claims
from elitecv.cli import _init
from elitecv.intake import IntakeError, apply_intake_proposal, intake_source
from elitecv.models import load_yaml

from test_wave4b import _proposal, _registered_workspace


@pytest.mark.parametrize("locator", ["owner@example.com", "a useful phrase", "lines:1-2\nsecret"])
def test_apply_rejects_private_or_free_form_locators(tmp_path, locator):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal["claims"][0]["evidence"][0]["locator"] = locator

    with pytest.raises(IntakeError, match="invalid_locator"):
        apply_intake_proposal(tmp_path, source_id, proposal)


def test_locator_ranges_are_bounded_and_ordered_in_proposals(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal["claims"][0]["evidence"][0]["locator"] = "lines:2-1"

    with pytest.raises(IntakeError, match="invalid_locator"):
        apply_intake_proposal(tmp_path, source_id, proposal)


@pytest.mark.parametrize("locator", ["page:0", "pages:1-2", "lines:1-2"])
def test_schema_and_runtime_reject_unsupported_locator_forms(tmp_path, locator):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    proposal["claims"][0]["evidence"][0]["locator"] = locator

    with pytest.raises(IntakeError, match="invalid_locator"):
        apply_intake_proposal(tmp_path, source_id, proposal)


def test_workspace_mutations_reject_concurrent_lock(tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    lock = tmp_path / "workspace" / ".elitecv.lock"
    lock.write_text("other-process", encoding="utf-8")

    with pytest.raises(IntakeError, match="workspace_busy"):
        apply_intake_proposal(tmp_path, source_id, proposal)

    sample = tmp_path / "sample.txt"
    sample.write_text("test", encoding="utf-8")
    with pytest.raises(IntakeError, match="workspace_busy"):
        intake_source(tmp_path, sample, target_role="Engineer", locale="en-US", hosted_processing="approved")


def test_apply_rolls_back_every_file_when_a_replace_fails(monkeypatch, tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    paths = [tmp_path / "data" / "claims.yml", tmp_path / "data" / "profile.yml"]
    originals = {path: path.read_bytes() for path in paths}
    original_artifact = (tmp_path / "workspace" / "intake" / f"{source_id}.json").read_bytes()
    original_replace = __import__("os").replace

    def fail_on_profile(src, dst):
        if str(dst).endswith("profile.yml"):
            raise OSError("injected replace failure")
        return original_replace(src, dst)

    monkeypatch.setattr("elitecv.intake.os.replace", fail_on_profile)
    with pytest.raises(OSError, match="injected replace failure"):
        apply_intake_proposal(tmp_path, source_id, proposal)

    assert {path: path.read_bytes() for path in paths} == originals
    assert (tmp_path / "workspace" / "intake" / f"{source_id}.json").read_bytes() == original_artifact
    assert not (tmp_path / "workspace" / "review" / f"{source_id}-questions.json").exists()


def test_approval_rolls_back_claims_when_variant_replace_fails(monkeypatch, tmp_path):
    source_id, fingerprint = _registered_workspace(tmp_path)
    proposal = _proposal(source_id)
    proposal["fingerprint"] = fingerprint
    apply_intake_proposal(tmp_path, source_id, proposal)
    claims_path = tmp_path / "data" / "claims.yml"
    variant_path = tmp_path / "data" / "variants" / "data-engineer.yml"
    originals = {path: path.read_bytes() for path in (claims_path, variant_path)}
    original_replace = __import__("os").replace

    def fail_on_variant(src, dst):
        if str(dst).endswith("data-engineer.yml"):
            raise OSError("injected replace failure")
        return original_replace(src, dst)

    monkeypatch.setattr("elitecv.intake.os.replace", fail_on_variant)
    with pytest.raises(OSError, match="injected replace failure"):
        approve_claims(tmp_path, source_id, "owner", ["claim.synthetic"], "shareable", [])

    assert {path: path.read_bytes() for path in (claims_path, variant_path)} == originals
    assert not list((tmp_path / "workspace" / "audit").glob("*.json"))
