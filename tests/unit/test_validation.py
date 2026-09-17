import pytest

from elitecv.validate import validate_documents


def _documents(*, claim_status="sourced", review_status="approved", disclosure="shareable"):
    sources = {
        "schema_version": 2,
        "sources": [
            {
                "id": "source.synthetic-notes",
                "type": "project-notes",
                "label": "Synthetic project notes",
                "path": "sources/project-notes.md",
                "confidentiality": "public",
                "collected_at": "2026-01-15",
                "fingerprint": None,
            }
        ],
    }
    claims = {
        "schema_version": 2,
        "claims": [
            {
                "id": "claim.rover.control",
                "statement": "Built control software for a synthetic rover.",
                "evidence": [
                    {
                        "source_id": "source.synthetic-notes",
                        "locator": "section:control",
                        "excerpt": None,
                    }
                ],
                "evidence_status": claim_status,
                "review_status": review_status,
                "disclosure": disclosure,
                "reviewed_by": "sample-owner",
                "reviewed_at": "2026-01-15",
                "questions": [],
            }
        ],
    }
    profile = {
        "schema_version": 2,
        "profile": {
            "id": "profile.synthetic",
            "name": "Alex Rivera",
            "headline": "Robotics Software Engineer",
            "headline_claim_ids": ["claim.rover.control"],
            "contact": {"email": "alex@example.com", "phone": None, "location": None, "links": []},
            "entries": [
                {
                    "id": "entry.rover",
                    "section": "experience",
                    "organization": "Synthetic Robotics Lab",
                    "role": "Software Engineer",
                    "location": "Remote",
                    "start_date": "2024-01",
                    "end_date": None,
                    "date_precision": "month",
                    "claim_ids": ["claim.rover.control"],
                    "bullets": [
                        {
                            "id": "bullet.rover.control",
                            "text": "Built control software for a synthetic rover.",
                            "claim_ids": ["claim.rover.control"],
                            "review_status": "approved",
                        }
                    ],
                }
            ],
            "skill_groups": [
                {
                    "id": "skills.technical",
                    "label": "Technical skills",
                    "items": [{"name": "Control systems", "claim_ids": ["claim.rover.control"]}],
                }
            ],
        },
    }
    variant = {
        "schema_version": 2,
        "id": "robotics-software",
        "target_role": "Robotics Software Intern",
        "locale": "en-US",
        "page_size": "letter",
        "page_target": 1,
        "sections": ["experience", "skills"],
        "include_entries": ["entry.rover"],
        "exclude_entries": [],
        "required_claim_ids": [],
        "allowed_disclosures": ["shareable"],
        "include_skill_groups": ["skills.technical"],
        "contact_fields": ["email"],
    }
    return sources, claims, profile, variant


def test_valid_bullet_has_complete_traceability():
    documents = _documents()

    result = validate_documents(*documents, strict=True)

    assert result.is_valid
    assert result.traceability_coverage == 1.0
    assert result.errors == []


def test_missing_claim_fails_with_bullet_and_claim_ids():
    sources, claims, profile, variant = _documents()
    profile["profile"]["entries"][0]["bullets"][0]["claim_ids"] = ["claim.missing"]

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert not result.is_valid
    assert any(issue.code == "missing_claim" for issue in result.errors)
    assert "bullet.rover.control" in str(result.errors)
    assert "claim.missing" in str(result.errors)


def test_pending_claim_cannot_enter_strict_build():
    documents = _documents(claim_status="unsupported", review_status="pending")

    result = validate_documents(*documents, strict=True)

    assert not result.is_valid
    assert any(issue.code == "claim_not_release_eligible" for issue in result.errors)


@pytest.mark.parametrize(
    ("claim_status", "review_status", "disclosure"),
    [
        ("conflicted", "pending", "shareable"),
        ("sourced", "rejected", "shareable"),
        ("sourced", "approved", "private"),
    ],
)
def test_conflicted_rejected_and_private_claims_block_release(
    claim_status, review_status, disclosure
):
    documents = _documents(
        claim_status=claim_status,
        review_status=review_status,
        disclosure=disclosure,
    )

    result = validate_documents(*documents, strict=True)

    assert not result.is_valid
    assert any(issue.code == "claim_not_release_eligible" for issue in result.errors)


@pytest.mark.parametrize("disclosure", ["private", "restricted"])
def test_non_shareable_claims_cannot_be_release_eligible_by_variant_policy(disclosure):
    sources, claims, profile, variant = _documents(disclosure=disclosure)
    variant["allowed_disclosures"] = [disclosure]

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert not result.is_valid
    assert any(issue.code == "claim_not_release_eligible" for issue in result.errors)


def test_draft_validation_keeps_non_release_claim_visible_as_warning():
    documents = _documents(claim_status="conflicted", review_status="pending")

    result = validate_documents(*documents, strict=False)

    assert result.is_valid
    assert any(issue.code == "claim_not_release_eligible" for issue in result.warnings)


def test_invalid_structured_date_and_url_are_actionable_errors():
    sources, claims, profile, variant = _documents()
    profile["profile"]["entries"][0]["start_date"] = "2024/01"
    profile["profile"]["contact"]["links"] = [{"label": "unsafe", "url": "javascript:alert(1)"}]
    variant["page_target"] = 0

    result = validate_documents(sources, claims, profile, variant, strict=True)

    codes = {issue.code for issue in result.errors}
    assert "invalid_date" in codes
    assert "invalid_url" in codes
    assert "invalid_page_target" in codes


def test_variant_required_claim_must_exist():
    documents = _documents()
    documents[-1]["required_claim_ids"] = ["claim.missing"]

    result = validate_documents(*documents, strict=True)

    assert any(issue.code == "required_claim_missing" for issue in result.errors)


def test_zero_selected_bullets_keep_numeric_coverage_compatibility():
    sources, claims, profile, variant = _documents()
    profile["profile"]["entries"][0]["bullets"] = []

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert result.traceability_coverage == 1.0
    assert result.selected_bullet_count == 0


def test_structured_provenance_and_disclosure_results_are_separate():
    result = validate_documents(*_documents(), strict=True)

    assert result.structured_provenance
    assert all({"path", "claim_ids", "eligible"} <= item.keys() for item in result.structured_provenance)
    assert result.disclosure_checks == [{"field": "email", "allowed": True}]


@pytest.mark.parametrize("field", ["headline_claim_ids", "claim_ids"])
def test_visible_structured_fields_require_eligible_claims(field):
    sources, claims, profile, variant = _documents(claim_status="unsupported", review_status="pending")
    if field == "headline_claim_ids":
        profile["profile"][field] = ["claim.rover.control"]
    else:
        profile["profile"]["entries"][0][field] = ["claim.rover.control"]

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert not result.is_valid
    assert any(issue.code == "structured_claim_not_release_eligible" for issue in result.errors)


def test_selected_skill_groups_and_items_require_existing_eligible_claims():
    sources, claims, profile, variant = _documents()
    variant["include_skill_groups"] = ["skills.missing"]
    result = validate_documents(sources, claims, profile, variant, strict=True)
    assert any(issue.code == "missing_skill_group" for issue in result.errors)

    variant["include_skill_groups"] = ["skills.technical"]
    profile["profile"]["skill_groups"][0]["items"][0]["claim_ids"] = []
    result = validate_documents(sources, claims, profile, variant, strict=True)
    assert any(issue.code == "skill_without_claim" for issue in result.errors)


def test_contact_fields_are_an_explicit_allowlist():
    sources, claims, profile, variant = _documents()
    variant["contact_fields"] = ["email", "fax"]

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert any(issue.code == "invalid_contact_field" for issue in result.errors)


def test_runtime_rejects_free_form_evidence_locators():
    sources, claims, profile, variant = _documents()
    claims["claims"][0]["evidence"][0]["locator"] = "private sentence from source"

    result = validate_documents(sources, claims, profile, variant, strict=True)

    assert any(issue.code == "invalid_locator" for issue in result.errors)
