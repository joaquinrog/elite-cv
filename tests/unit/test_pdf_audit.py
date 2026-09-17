from elitecv.pdf_audit import audit_pdf_text
from elitecv.build import _expected_pdf_fields, _protected_pdf_fields
from elitecv.locale import format_date_range


def test_pdf_audit_returns_safe_quality_findings_without_text():
    result = audit_pdf_text(
        "Alex Rivera\nRobotics Software Engineer\n",
        expected_fields={"name": "Alex Rivera", "headline": "Robotics Software Engineer"},
        protected_fields={"headline": "Robotics Software Engineer"},
    )

    assert result["status"] == "pass"
    assert result["findings"] == []
    assert "Alex Rivera" not in str(result)


def test_pdf_audit_classifies_private_safe_text_problems():
    result = audit_pdf_text(
        "A\ufffd\ufdd0\nRobotics Software-\nEngineer\n",
        expected_fields={"headline": "Robotics Software Engineer", "missing": "Missing"},
        protected_fields={"headline": "Robotics Software Engineer"},
    )

    assert result["status"] == "fail"
    assert {finding["code"] for finding in result["findings"]} == {
        "text_too_short",
        "replacement_character",
        "noncharacter",
        "expected_text_missing",
        "protected_field_hyphenation",
    }


def test_build_pdf_protection_uses_selected_skill_groups_not_v1_skills():
    profile = {
        "headline": "Synthetic headline",
        "skill_groups": [
            {"id": "skills.selected", "label": "Selected", "items": [{"name": "Python"}]},
            {"id": "skills.omitted", "label": "Omitted", "items": [{"name": "Legacy Tool"}]},
        ],
        "skills": ["v1 skill that must be ignored"],
    }
    variant = {"include_skill_groups": ["skills.selected"]}

    protected = _protected_pdf_fields(profile, variant, [])

    assert "Python" in protected.values()
    assert "Legacy Tool" not in protected.values()
    assert "v1 skill that must be ignored" not in protected.values()


def test_pdf_audit_requires_selected_rendered_sections_dates_contact_and_skills():
    expected = {
        "name": "Alex Rivera",
        "headline": "Robotics Software Engineer",
        "section.experience": "Experience",
        "entry.rover.role": "Software Engineer",
        "entry.rover.organization": "Synthetic Robotics Lab",
        "entry.rover.dates": format_date_range("2024-01", None, "en-US"),
        "contact.email": "alex@example.com",
        "skill.technical": "Control systems",
    }
    result = audit_pdf_text(
        "Alex Rivera\nRobotics Software Engineer\nExperience\nSoftware Engineer | Synthetic Robotics Lab\n"
        "January 2024 - Present\nalex@example.com\nControl systems\n",
        expected_fields=expected,
        protected_fields=expected,
    )

    assert result["status"] == "pass"


def test_pdf_audit_reports_missing_expected_text_without_exposing_values():
    result = audit_pdf_text(
        "Alex Rivera\nRobotics Software Engineer\n",
        expected_fields={"section.experience": "Experience", "contact.email": "secret@example.com"},
        protected_fields={"section.experience": "Experience", "contact.email": "secret@example.com"},
    )

    assert result["status"] == "fail"
    assert {item["code"] for item in result["findings"]} == {"expected_text_missing"}
    assert "secret@example.com" not in str(result)


def test_build_expected_text_covers_visible_document_categories():
    profile = {
        "name": "Alex Rivera",
        "headline": "Robotics Engineer",
        "contact": {
            "email": "alex@example.com",
            "phone": None,
            "location": None,
            "links": [{"label": "Portfolio", "url": "https://example.com"}],
        },
        "skill_groups": [
            {
                "id": "skills.technical",
                "label": "Technical skills",
                "items": [{"name": "Control systems"}],
            }
        ],
    }
    variant = {
        "locale": "en-US",
        "sections": ["experience", "skills"],
        "include_skill_groups": ["skills.technical"],
        "contact_fields": ["email", "links"],
    }
    entries = [
        {
            "id": "entry.rover",
            "section": "experience",
            "role": "Software Engineer",
            "organization": "Synthetic Robotics Lab",
            "location": "Remote",
            "start_date": "2024-01",
            "end_date": None,
        }
    ]

    expected = _expected_pdf_fields(profile, variant, entries)

    assert set(expected.values()) >= {
        "Alex Rivera",
        "Robotics Engineer",
        "Experience",
        "Software Engineer",
        "Synthetic Robotics Lab",
        "January 2024 - Present",
        "alex@example.com",
        "Portfolio",
        "Technical skills",
        "Control systems",
    }
