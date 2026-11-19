
from pathlib import Path

import pymupdf
from pydantic import BaseModel, Field


class PageText(BaseModel):
    page_number: int = Field(ge=1)
    text: str


def extract_pdf_pages(pdf_path: str | Path) -> list[PageText]:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    pages = []

    with pymupdf.open(str(pdf_path)) as document:
        for index, page in enumerate(document):
            text = page.get_text(
                "text",
                sort=True
            ).strip()

            pages.append(
                PageText(
                    page_number=index + 1,
                    text=text
                )
            )

    return pages


if __name__ == "__main__":
    pages = extract_pdf_pages(
        "data/reports/sample_report.pdf"
    )

    for page in pages:
        print(f"\n{'=' * 50}")
        print(f"PAGE {page.page_number}")
        print(f"{'=' * 50}")
        print(page.text)
