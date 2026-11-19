
from app.models import InspectionExtraction, PollutantFinding
from app.pdf_parser import PageText, extract_pdf_pages
from app.validator import validate_evidence


def build_extraction(concentration=2.5):
    return InspectionExtraction(
        building_name="Residential Building A",
        inspection_date="2025-06-15",
        findings=[
            PollutantFinding(
                component="Ceiling Panel",
                location="First Floor, Room 101",
                material="Fiber Cement",
                substance="Asbestos",
                concentration=concentration,
                unit="%",
                sample_id="AS-101",
                result="positive",
                page_number=1,
                evidence_text=(
                    "Location: First Floor, Room 101\n"
                    "Building Component: Ceiling Panel\n"
                    "Material: Fiber Cement\n"
                    "Hazardous Substance: Asbestos\n"
                    "Sample ID: AS-101\n"
                    "Concentration: 2.5%\n"
                    "Laboratory Result: Positive"
                )
            )
        ]
    )


def test_correct_extraction():
    pages = extract_pdf_pages(
        "data/reports/sample_report.pdf"
    )

    errors = validate_evidence(
        build_extraction(),
        pages
    )

    assert errors == []


def test_incorrect_concentration():
    pages = extract_pdf_pages(
        "data/reports/sample_report.pdf"
    )

    errors = validate_evidence(
        build_extraction(concentration=8.5),
        pages
    )

    assert any(
        "concentration mismatch" in error
        for error in errors
    )


def test_invalid_page_number():
    pages = extract_pdf_pages(
        "data/reports/sample_report.pdf"
    )

    extraction = build_extraction()
    extraction.findings[0].page_number = 99

    errors = validate_evidence(
        extraction,
        pages
    )

    assert any(
        "does not exist" in error
        for error in errors
    )


def test_unsupported_evidence():
    pages = [
        PageText(
            page_number=1,
            text="No pollutant findings reported."
        )
    ]

    errors = validate_evidence(
        build_extraction(),
        pages
    )

    assert any(
        "evidence not found" in error
        for error in errors
    )
