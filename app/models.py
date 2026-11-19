
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PollutantFinding(BaseModel):
    component: str = Field(min_length=1)
    location: str | None = None
    material: str | None = None
    substance: str = Field(min_length=1)
    concentration: float | None = Field(
        default=None,
        ge=0
    )
    unit: str | None = None
    sample_id: str | None = None
    result: Literal[
        "positive",
        "negative",
        "unknown"
    ] = "unknown"
    page_number: int = Field(ge=1)
    evidence_text: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_measurement(self):
        if self.concentration is not None and not self.unit:
            raise ValueError(
                "A measurement unit is required "
                "when concentration is provided"
            )

        return self


class InspectionExtraction(BaseModel):
    building_name: str | None = None
    inspection_date: date | None = None
    findings: list[PollutantFinding] = Field(
        default_factory=list
    )
