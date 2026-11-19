
import pytest

from pydantic import ValidationError

from app.models import (
    PollutantFinding,
    InspectionExtraction
)


def test_valid_pollutant_finding():
    finding = PollutantFinding(
        component="Ceiling Panel",
        location="First Floor, Room 101",
        material="Fiber Cement",
        substance="Asbestos",
        concentration=2.5,
        unit="%",
        sample_id="AS-101",
        result="positive",
        page_number=1,
        evidence_text="Hazardous Substance: Asbestos"
    )

    assert finding.component == "Ceiling Panel"
    assert finding.concentration == 2.5
    assert finding.unit == "%"
    assert finding.result == "positive"


def test_negative_concentration():
    with pytest.raises(ValidationError):
        PollutantFinding(
            component="Ceiling Panel",
            substance="Asbestos",
            concentration=-2.5,
            unit="%",
            page_number=1,
            evidence_text="Asbestos"
        )


def test_missing_measurement_unit():
    with pytest.raises(ValidationError):
        PollutantFinding(
            component="Ceiling Panel",
            substance="Asbestos",
            concentration=2.5,
            page_number=1,
            evidence_text="Asbestos 2.5%"
        )


def test_complete_inspection():
    finding = PollutantFinding(
        component="Ceiling Panel",
        substance="Asbestos",
        concentration=2.5,
        unit="%",
        page_number=1,
        evidence_text="Asbestos 2.5%"
    )

    inspection = InspectionExtraction(
        building_name="Residential Building A",
        inspection_date="2025-06-15",
        findings=[finding]
    )

    assert inspection.building_name == "Residential Building A"
    assert len(inspection.findings) == 1
    assert inspection.findings[0].substance == "Asbestos"
