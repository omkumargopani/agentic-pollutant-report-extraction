
from pathlib import Path

from dotenv import load_dotenv
from langfuse import get_client, observe
from pydantic_ai import Agent


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env", override=True)

langfuse = get_client()

Agent.instrument_all()

from app.agent import (
    ExtractionDependencies,
    extraction_agent
)
from app.pdf_parser import extract_pdf_pages
from app.validator import validate_evidence
from app.graph import PollutantGraph


@observe(name="pollutant-report-extraction")
def process_report(pdf_path: Path):
    print("Step 1: Reading PDF report...")

    pages = extract_pdf_pages(pdf_path)

    if not pages or not any(page.text for page in pages):
        raise ValueError("No extractable PDF text found")

    print(f"Extracted {len(pages)} pages")

    document_text = "\n\n".join(
        f"PAGE {page.page_number}\n{page.text}"
        for page in pages
    )

    dependencies = ExtractionDependencies(pages=pages)

    print("Step 2: Running GPT extraction agent...")

    result = extraction_agent.run_sync(
        "Extract all pollutant findings from "
        "the following inspection report:\n\n"
        + document_text,
        deps=dependencies
    )

    extraction = result.output

    print(f"Extracted {len(extraction.findings)} findings")

    print("Step 3: Validating source evidence...")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="source-evidence-validation"
    ):
        validation_errors = validate_evidence(
            extraction,
            pages
        )

        if validation_errors:
            raise ValueError(
                "Source validation failed: "
                + "; ".join(validation_errors)
            )

    print("Source validation passed")

    print("Step 4: Saving structured JSON...")

    output_path = (
        BASE_DIR / "outputs" / f"{pdf_path.stem}.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        extraction.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print(f"JSON saved to {output_path}")

    print("Step 5: Saving findings to Neo4j...")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="neo4j-storage"
    ):
        graph = PollutantGraph()

        try:
            graph.create_constraints()
            graph.save_extraction(
                extraction=extraction,
                pdf_path=pdf_path
            )
        finally:
            graph.close()

    print("Pipeline completed successfully!")


def main():
    pdf_path = (
        BASE_DIR / "data" / "reports" / "sample_report.pdf"
    )

    try:
        process_report(pdf_path)
    finally:
        langfuse.flush()


if __name__ == "__main__":
    main()
