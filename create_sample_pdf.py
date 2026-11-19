
from pathlib import Path

import pymupdf


output_path = Path("data/reports/sample_report.pdf")
output_path.parent.mkdir(parents=True, exist_ok=True)

document = pymupdf.open()

pages = [
    """BUILDING POLLUTANT INSPECTION REPORT

Building Name: Residential Building A
Inspection Date: 2025-06-15
Building Address: 123 Example Street

INSPECTION FINDING 1

Location: First Floor, Room 101
Building Component: Ceiling Panel
Material: Fiber Cement
Hazardous Substance: Asbestos
Sample ID: AS-101
Concentration: 2.5%
Laboratory Result: Positive
""",
    """INSPECTION FINDING 2

Location: Ground Floor, Room 005
Building Component: Wall Paint
Material: Paint Coating
Hazardous Substance: Lead
Sample ID: PB-201
Concentration: 1200 mg/kg
Laboratory Result: Positive
""",
    """INSPECTION FINDING 3

Location: Basement
Building Component: Pipe Insulation
Material: Insulation
Hazardous Substance: Asbestos
Sample ID: AS-102
Concentration: 4.2%
Laboratory Result: Positive
"""
]

for content in pages:
    page = document.new_page()
    page.insert_text(
        (50, 60),
        content,
        fontsize=11,
        lineheight=1.5
    )

document.save(str(output_path))
document.close()

print(f"Created: {output_path}")
