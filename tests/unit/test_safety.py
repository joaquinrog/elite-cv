from elitecv.safety import scan_public_tree


def test_public_scan_accepts_synthetic_fixture(tmp_path):
    (tmp_path / "README.md").write_text("Alex Rivera alex@example.com\n", encoding="utf-8")
    (tmp_path / "examples").mkdir()
    (tmp_path / "examples" / "sample.yml").write_text("schema_version: 1\n", encoding="utf-8")

    findings = scan_public_tree(tmp_path)

    assert findings == []


def test_public_scan_rejects_secret_and_private_path(tmp_path):
    private_dir = tmp_path / "sources" / "private"
    private_dir.mkdir(parents=True)
    (private_dir / "notes.txt").write_text("do not publish\n", encoding="utf-8")
    (tmp_path / "leaked.env").write_text(
        "AWS_SECRET_ACCESS_KEY=not-a-real-secret\n", encoding="utf-8"
    )

    findings = scan_public_tree(tmp_path)

    codes = {finding.code for finding in findings}
    assert "forbidden_path" in codes
    assert "secret_pattern" in codes


def test_public_scan_detects_formatted_phone_but_ignores_dates_and_ids(tmp_path):
    (tmp_path / "README.md").write_text(
        "Reviewed 2026-01-16; fixture id 1234567890; call +1 (555) 123-4567.\n",
        encoding="utf-8",
    )

    findings = scan_public_tree(tmp_path)

    assert [finding.code for finding in findings] == ["phone_pattern"]


def test_public_scan_rejects_local_only_paths_at_any_depth(tmp_path):
    generated = tmp_path / "examples" / "sample" / "dist"
    generated.mkdir(parents=True)
    (generated / "cv.pdf").write_bytes(b"synthetic")

    findings = scan_public_tree(tmp_path)

    assert any(finding.code == "forbidden_path" for finding in findings)


def test_public_scan_rejects_personal_workspace_paths(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "profile.yml").write_text("name: Private Person\n", encoding="utf-8")
    raw_sources = tmp_path / "sources" / "raw"
    raw_sources.mkdir(parents=True)
    (raw_sources / "resume.txt").write_text("private source\n", encoding="utf-8")

    findings = scan_public_tree(tmp_path)

    paths = {finding.path for finding in findings if finding.code == "forbidden_path"}
    assert "data/profile.yml" in paths
    assert "sources/raw/resume.txt" in paths


def test_public_scan_checks_package_code_and_html_reports(tmp_path):
    package = tmp_path / "elitecv"
    package.mkdir()
    (package / "settings.py").write_text(
        "API_KEY=supersecretvalue123\n", encoding="utf-8"
    )
    (tmp_path / "report.html").write_text(
        "person@private.invalid\n", encoding="utf-8"
    )

    findings = scan_public_tree(tmp_path)

    codes = {finding.code for finding in findings}
    assert "secret_pattern" in codes
    assert "private_email" in codes


def test_public_scan_rejects_an_unapproved_binary_artifact(tmp_path):
    (tmp_path / "leaked.pdf").write_bytes(b"not a public sample")

    findings = scan_public_tree(tmp_path)

    assert any(
        finding.code == "unexpected_binary" and finding.path == "leaked.pdf"
        for finding in findings
    )


def test_public_scan_treats_license_as_text(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    assert scan_public_tree(tmp_path) == []


def test_public_scan_does_not_match_token_prefixes_in_source_code(tmp_path):
    (tmp_path / "scanner.py").write_text(
        'prefixes = ("ghp_", "github_pat_", "sk-")\n', encoding="utf-8"
    )

    assert scan_public_tree(tmp_path) == []


def test_public_scan_detects_complete_github_token(tmp_path):
    (tmp_path / "leaked.txt").write_text(
        "ghp_" + "a" * 36 + "\n", encoding="utf-8"
    )

    assert any(
        finding.code == "secret_pattern" for finding in scan_public_tree(tmp_path)
    )
