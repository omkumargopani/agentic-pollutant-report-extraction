
import json
from pathlib import Path

from app.models import InspectionExtraction


FIELDS = [
    "component",
    "location",
    "material",
    "substance",
    "concentration",
    "unit",
    "sample_id",
    "result",
    "page_number"
]


def normalize(value):
    if isinstance(value, str):
        return " ".join(value.casefold().split())

    return value


def same_value(first, second):
    if isinstance(first, (float, int)) and isinstance(
        second, (float, int)
    ):
        return abs(first - second) <= 1e-9

    return normalize(first) == normalize(second)


def match_findings(predicted, expected):
    matches = []
    unmatched_predictions = set(range(len(predicted)))
    unmatched_expected = set(range(len(expected)))

    for expected_index, reference in enumerate(expected):
        candidates = []

        for predicted_index in unmatched_predictions:
            candidate = predicted[predicted_index]

            if reference.sample_id and candidate.sample_id:
                identity_match = (
                    normalize(reference.sample_id)
                    == normalize(candidate.sample_id)
                    and reference.page_number
                    == candidate.page_number
                )
            else:
                identity_match = (
                    normalize(reference.component)
                    == normalize(candidate.component)
                    and normalize(reference.location)
                    == normalize(candidate.location)
                    and reference.page_number
                    == candidate.page_number
                )

            if identity_match:
                candidates.append(predicted_index)

        if candidates:
            best_index = max(
                candidates,
                key=lambda i: sum(
                    same_value(
                        getattr(predicted[i], field),
                        getattr(reference, field)
                    )
                    for field in FIELDS
                )
            )

            matches.append((
                predicted[best_index],
                reference
            ))

            unmatched_predictions.remove(best_index)
            unmatched_expected.remove(expected_index)

    return matches, unmatched_predictions, unmatched_expected


def evaluate_extraction(
    predicted: InspectionExtraction,
    expected: InspectionExtraction
):
    matches, unmatched_pred, unmatched_ref = match_findings(
        predicted.findings,
        expected.findings
    )

    correct = sum(
        same_value(p.component, r.component)
        and same_value(p.substance, r.substance)
        for p, r in matches
    )

    predicted_count = len(predicted.findings)
    expected_count = len(expected.findings)

    precision = (
        correct / predicted_count
        if predicted_count
        else 1.0 if expected_count == 0 else 0.0
    )

    recall = (
        correct / expected_count
        if expected_count
        else 1.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    field_accuracy = {}

    for field in FIELDS:
        if matches:
            field_accuracy[field] = round(
                sum(
                    same_value(
                        getattr(prediction, field),
                        getattr(reference, field)
                    )
                    for prediction, reference in matches
                ) / len(matches),
                4
            )
        else:
            field_accuracy[field] = None

    return {
        "predicted_findings": predicted_count,
        "expected_findings": expected_count,
        "matched_findings": len(matches),
        "correct_findings": correct,
        "unmatched_predictions": len(unmatched_pred),
        "unmatched_references": len(unmatched_ref),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "field_accuracy": field_accuracy
    }


def main():
    predicted_path = Path("outputs/sample_report.json")
    expected_path = Path(
        "data/ground_truth/sample_report.json"
    )

    predicted = InspectionExtraction.model_validate_json(
        predicted_path.read_text(encoding="utf-8")
    )

    expected = InspectionExtraction.model_validate_json(
        expected_path.read_text(encoding="utf-8")
    )

    results = evaluate_extraction(predicted, expected)

    output_path = Path("outputs/evaluation_results.json")

    output_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(results, indent=2))
    print(f"Evaluation saved to {output_path}")


if __name__ == "__main__":
    main()
