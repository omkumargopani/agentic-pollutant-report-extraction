
from app.evaluation import evaluate_extraction
from app.models import InspectionExtraction, PollutantFinding


def build_finding(substance="Asbestos", concentration=2.5):
    return PollutantFinding(
        component="Ceiling Panel",
        location="Room 101",
        material="Fiber Cement",
        substance=substance,
        concentration=concentration,
        unit="%",
        sample_id="AS-101",
        result="positive",
        page_number=1,
        evidence_text="Hazardous Substance: Asbestos"
    )


def test_perfect_extraction():
    reference = InspectionExtraction(
        findings=[build_finding()]
    )

    predicted = InspectionExtraction(
        findings=[build_finding()]
    )

    scores = evaluate_extraction(predicted, reference)

    assert scores["precision"] == 1.0
    assert scores["recall"] == 1.0
    assert scores["f1"] == 1.0


def test_wrong_substance():
    reference = InspectionExtraction(
        findings=[build_finding()]
    )

    predicted = InspectionExtraction(
        findings=[build_finding(substance="Lead")]
    )

    scores = evaluate_extraction(predicted, reference)

    assert scores["f1"] == 0.0
    assert scores["field_accuracy"]["substance"] == 0.0


def test_wrong_concentration():
    reference = InspectionExtraction(
        findings=[build_finding()]
    )

    predicted = InspectionExtraction(
        findings=[build_finding(concentration=8.5)]
    )

    scores = evaluate_extraction(predicted, reference)

    assert scores["f1"] == 1.0
    assert scores["field_accuracy"]["concentration"] == 0.0


def test_missing_finding():
    reference = InspectionExtraction(
        findings=[build_finding()]
    )

    predicted = InspectionExtraction(
        findings=[]
    )

    scores = evaluate_extraction(predicted, reference)

    assert scores["recall"] == 0.0
    assert scores["f1"] == 0.0
