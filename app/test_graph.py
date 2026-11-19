
from pathlib import Path

from app.graph import PollutantGraph
from app.models import InspectionExtraction


def main():
    json_path = Path("outputs/sample_report.json")
    pdf_path = Path("data/reports/sample_report.pdf")

    extraction = InspectionExtraction.model_validate_json(
        json_path.read_text(encoding="utf-8")
    )

    print(f"Loaded {len(extraction.findings)} findings")

    graph = PollutantGraph()

    try:
        graph.create_constraints()
        graph.save_extraction(
            extraction=extraction,
            pdf_path=pdf_path
        )
    finally:
        graph.close()


if __name__ == "__main__":
    main()
