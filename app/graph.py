
import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

from app.models import InspectionExtraction


load_dotenv(
    Path(__file__).resolve().parent.parent / ".env",
    override=True
)


class PollutantGraph:
    def __init__(self):
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        self.driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(
                os.environ["NEO4J_USERNAME"],
                os.environ["NEO4J_PASSWORD"]
            )
        )

        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_constraints(self):
        constraints = [
            "CREATE CONSTRAINT building_id IF NOT EXISTS FOR (b:Building) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (f:Finding) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:InspectionDocument) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT substance_name IF NOT EXISTS FOR (s:Substance) REQUIRE s.name IS UNIQUE"
        ]

        for query in constraints:
            self.driver.execute_query(
                query,
                database_=self.database
            )

    def save_extraction(
        self,
        extraction: InspectionExtraction,
        pdf_path: str | Path
    ):
        pdf_path = Path(pdf_path)

        document_id = hashlib.sha256(
            pdf_path.read_bytes()
        ).hexdigest()

        building_name = (
            extraction.building_name
            or f"Unknown Building {document_id[:12]}"
        )

        building_id = hashlib.sha256(
            building_name.strip().casefold().encode()
        ).hexdigest()

        findings = []

        for index, finding in enumerate(extraction.findings):
            component_key = "|".join([
                building_id,
                (finding.location or "").strip().casefold(),
                finding.component.strip().casefold()
            ])

            component_id = hashlib.sha256(
                component_key.encode()
            ).hexdigest()

            data = finding.model_dump()

            data["component_id"] = component_id
            data["finding_id"] = f"{document_id}:{index}"
            data["substance_key"] = (
                finding.substance.strip().casefold()
            )

            findings.append(data)

        query = """
        MERGE (b:Building {id: $building_id})
        SET b.name = $building_name

        MERGE (d:InspectionDocument {id: $document_id})
        SET d.filename = $filename,
            d.inspection_date = $inspection_date

        MERGE (b)-[:HAS_DOCUMENT]->(d)

        WITH b, d
        UNWIND $findings AS item

        MERGE (c:Component {id: item.component_id})
        SET c.name = item.component,
            c.location = item.location,
            c.material = item.material

        MERGE (b)-[:HAS_COMPONENT]->(c)

        MERGE (s:Substance {name: item.substance_key})
        SET s.display_name = item.substance

        MERGE (f:Finding {id: item.finding_id})
        SET f.concentration = item.concentration,
            f.unit = item.unit,
            f.sample_id = item.sample_id,
            f.result = item.result,
            f.page_number = item.page_number,
            f.evidence_text = item.evidence_text

        MERGE (c)-[:HAS_FINDING]->(f)
        MERGE (f)-[:DETECTS]->(s)
        MERGE (f)-[:REPORTED_IN]->(d)
        """

        self.driver.execute_query(
            query,
            building_id=building_id,
            building_name=building_name,
            document_id=document_id,
            filename=pdf_path.name,
            inspection_date=(
                extraction.inspection_date.isoformat()
                if extraction.inspection_date
                else None
            ),
            findings=findings,
            database_=self.database
        )

        print(f"Saved {len(findings)} findings to Neo4j")
