
import re

from app.models import InspectionExtraction
from app.pdf_parser import PageText


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def get_field(evidence: str, label: str) -> str | None:
    pattern = rf"(?im)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$"
    match = re.search(pattern, evidence)

    return match.group(1).strip() if match else None


def validate_evidence(
    extraction: InspectionExtraction,
    pages: list[PageText]
) -> list[str]:
    errors = []

    page_lookup = {
        page.page_number: page.text
        for page in pages
    }

    fields = {
        "component": "Building Component",
        "location": "Location",
        "material": "Material",
        "substance": "Hazardous Substance",
        "sample_id": "Sample ID",
        "result": "Laboratory Result"
    }

    for index, finding in enumerate(
        extraction.findings,
        start=1
    ):
        prefix = f"Finding {index}"
        page_text = page_lookup.get(finding.page_number)

        if page_text is None:
            errors.append(
                f"{prefix}: page {finding.page_number} does not exist"
            )
            continue

        evidence = finding.evidence_text

        if normalize_text(evidence) not in normalize_text(page_text):
            errors.append(
                f"{prefix}: evidence not found on page "
                f"{finding.page_number}"
            )
            continue

        for attribute, label in fields.items():
            expected = getattr(finding, attribute)

            if expected is None:
                continue

            actual = get_field(evidence, label)

            if actual is None:
                errors.append(
                    f"{prefix}: missing evidence for {attribute}"
                )
                continue

            if normalize_text(str(expected)) != normalize_text(actual):
                errors.append(
                    f"{prefix}: {attribute} mismatch: "
                    f"extracted={expected}, source={actual}"
                )

        measurement = get_field(evidence, "Concentration")

        if finding.concentration is not None:
            if measurement is None:
                errors.append(
                    f"{prefix}: concentration evidence missing"
                )
            else:
                match = re.fullmatch(
                    r"([0-9]+(?:\.[0-9]+)?)\s*(.+)",
                    measurement
                )

                if match is None:
                    errors.append(
                        f"{prefix}: unsupported measurement format"
                    )
                else:
                    actual_value = float(match.group(1))
                    actual_unit = match.group(2).strip()

                    if not (
                        abs(actual_value - finding.concentration)
                        <= 1e-9
                    ):
                        errors.append(
                            f"{prefix}: concentration mismatch: "
                            f"extracted={finding.concentration}, "
                            f"source={actual_value}"
                        )

                    if normalize_text(actual_unit) != normalize_text(
                        finding.unit or ""
                    ):
                        errors.append(
                            f"{prefix}: measurement unit mismatch"
                        )

    return errors
