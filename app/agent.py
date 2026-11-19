
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from app.models import InspectionExtraction
from app.pdf_parser import PageText


load_dotenv()


@dataclass
class ExtractionDependencies:
    pages: list[PageText]


extraction_agent = Agent(
    os.getenv("OPENAI_MODEL", "openai:gpt-4.1-mini"),
    deps_type=ExtractionDependencies,
    output_type=InspectionExtraction,
    instructions="""
    You are an expert assistant for extracting
    hazardous substances from building reports.

    Extract every reported pollutant finding.

    For each finding identify:
    - Building component
    - Location
    - Material
    - Hazardous substance
    - Concentration and original unit
    - Laboratory sample ID
    - Laboratory result
    - Source page number
    - Exact supporting source text

    Also extract the building name and
    inspection date.

    Never invent information.
    Use null for missing optional information.

    Copy evidence_text exactly from the report.
    Do not change numerical measurements.

    Use document retrieval tools when necessary.
    """
)


@extraction_agent.tool
def search_report(
    ctx: RunContext[ExtractionDependencies],
    keyword: str
) -> list[dict]:
    """Find report pages containing a search keyword."""
    results = []

    for page in ctx.deps.pages:
        if keyword.casefold() in page.text.casefold():
            results.append({
                "page_number": page.page_number,
                "text": page.text[:4000]
            })

    return results


@extraction_agent.tool
def get_page_text(
    ctx: RunContext[ExtractionDependencies],
    page_number: int
) -> str:
    """Retrieve the full text from a report page."""
    for page in ctx.deps.pages:
        if page.page_number == page_number:
            return page.text

    return "Page not found"
