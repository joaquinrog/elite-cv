from elitecv.safety import scan_public_tree


def test_private_key_fixture_is_blocked(tmp_path):
    (tmp_path / "leaked.txt").write_text(
        "-----BEGIN RSA PRIVATE KEY-----\nplaceholder\n",
        encoding="utf-8",
    )

    findings = scan_public_tree(tmp_path)

    assert any(finding.code == "secret_pattern" for finding in findings)


def test_synthetic_contact_and_date_are_allowed(tmp_path):
    (tmp_path / "sample.md").write_text(
        "alex@example.com; reviewed 2026-01-16; fixture id 1234567890\n",
        encoding="utf-8",
    )

    assert scan_public_tree(tmp_path) == []
