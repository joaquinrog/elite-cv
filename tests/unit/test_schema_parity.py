from pathlib import Path
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from elitecv.models import load_workspace
from elitecv.validate import validate_documents


ROOT = Path(__file__).parents[2]
SCHEMAS = {
    name: json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    for name in ("sources", "claims", "profile", "variant")
}


@pytest.mark.parametrize("fixture_root,target", [
    (ROOT / "examples" / "synthetic-profile", "robotics-software"),
    (ROOT / "examples" / "synthetic-profile", "ai-internship"),
    (ROOT / "examples" / "synthetic-junior-design", "diseno-junior"),
])
def test_public_fixtures_match_v2_json_schemas_and_runtime(fixture_root, target):
    documents = load_workspace(fixture_root, target)
    for name in SCHEMAS:
        document = getattr(documents, name)
        errors = sorted(Draft202012Validator(SCHEMAS[name]).iter_errors(document), key=str)
        assert not errors, f"{name}: {errors}"
    assert validate_documents(
        documents.sources, documents.claims, documents.profile, documents.variant, strict=True
    ).is_valid


def test_schemas_reject_v1_without_runtime_compatibility():
    for schema in SCHEMAS.values():
        with pytest.raises(Exception):
            Draft202012Validator(schema).validate({"schema_version": 1})


def _valid_documents():
    documents = load_workspace(ROOT / "examples" / "synthetic-profile", "robotics-software")
    return [documents.sources, documents.claims, documents.profile, documents.variant]


@pytest.mark.parametrize(
    ("document_index", "mutate"),
    [
        (0, lambda document: document.pop("sources")),
        (0, lambda document: document["sources"][0].update({"extra": True})),
        (0, lambda document: document["sources"][0].pop("label")),
        (1, lambda document: document.update({"extra": True})),
        (1, lambda document: document["claims"][0].update({"extra": True})),
        (1, lambda document: document["claims"][0].pop("statement")),
        (2, lambda document: document["profile"].pop("headline")),
        (2, lambda document: document["profile"]["contact"].pop("email")),
        (2, lambda document: document["profile"]["entries"][0].pop("date_precision")),
        (2, lambda document: document["profile"]["entries"][0].update({"organization": 7})),
        (2, lambda document: document["profile"]["entries"][0].update({"extra": True})),
        (2, lambda document: document["profile"]["skill_groups"][0]["items"][0].update({"extra": True})),
        (3, lambda document: document.update({"extra": True})),
        (3, lambda document: document.update({"sections": "experience"})),
        (3, lambda document: document.update({"contact_fields": ["fax"]})),
    ],
)
def test_invalid_profile_and_variant_documents_are_rejected_by_schema_and_runtime(
    document_index, mutate
):
    documents = _valid_documents()
    mutate(documents[document_index])
    name = ("sources", "claims", "profile", "variant")[document_index]

    schema_errors = list(Draft202012Validator(SCHEMAS[name]).iter_errors(documents[document_index]))
    runtime = validate_documents(*documents, strict=True)

    assert schema_errors
    assert not runtime.is_valid


@pytest.mark.parametrize("date_precision,date_value", [("year", "2024-01"), ("month", "2024")])
def test_date_precision_must_match_date_shape_in_both_contracts(date_precision, date_value):
    documents = _valid_documents()
    documents[2]["profile"]["entries"][0]["date_precision"] = date_precision
    documents[2]["profile"]["entries"][0]["start_date"] = date_value

    schema_errors = list(Draft202012Validator(SCHEMAS["profile"]).iter_errors(documents[2]))
    runtime = validate_documents(*documents, strict=True)

    assert schema_errors
    assert not runtime.is_valid
    assert any(issue.code == "date_precision_mismatch" for issue in runtime.errors)


@pytest.mark.parametrize("locator", ["page:0", "pages:1-2", "lines:1-2", "private sentence"])
def test_locator_contract_rejects_the_same_unsafe_forms(locator):
    documents = _valid_documents()
    documents[1]["claims"][0]["evidence"][0]["locator"] = locator

    schema_errors = list(Draft202012Validator(SCHEMAS["claims"]).iter_errors(documents[1]))
    runtime = validate_documents(*documents, strict=True)

    assert schema_errors
    assert any(issue.code == "invalid_locator" for issue in runtime.errors)
