from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PositiveFloat, PositiveInt, model_validator


class ConstructionPhase(str, Enum):
    foundation = "foundation"
    structure = "structure"
    roofing = "roofing"
    finishing = "finishing"


class InputProject(BaseModel):
    built_up_area_sqft: PositiveFloat = Field(..., description="Total built-up area in square feet")
    floors: PositiveInt = Field(..., description="Number of floors")
    timeline_weeks: PositiveInt = Field(..., description="Planned project timeline in weeks")


class WageConfig(BaseModel):
    mason_daily_inr: PositiveFloat = 900
    helper_daily_inr: PositiveFloat = 650
    carpenter_daily_inr: PositiveFloat = 1000
    bar_bender_daily_inr: PositiveFloat = 1000
    electrician_daily_inr: PositiveFloat = 1100
    plumber_daily_inr: PositiveFloat = 1050
    painter_daily_inr: PositiveFloat = 900


class MaterialRateConfig(BaseModel):
    cement_bag_inr: PositiveFloat = 420
    steel_kg_inr: PositiveFloat = 72
    sand_cuft_inr: PositiveFloat = 55
    aggregate_cuft_inr: PositiveFloat = 45
    brick_per_piece_inr: PositiveFloat = 8.5


class CompressionConfig(BaseModel):
    target_timeline_weeks: PositiveInt


class EstimationRequest(BaseModel):
    project: InputProject
    wages: WageConfig = Field(default_factory=WageConfig)
    materials: MaterialRateConfig = Field(default_factory=MaterialRateConfig)
    compression: Optional[CompressionConfig] = None

    @model_validator(mode="after")
    def validate_compression_timeline(self) -> "EstimationRequest":
        if self.compression and self.compression.target_timeline_weeks >= self.project.timeline_weeks:
            raise ValueError("compression.target_timeline_weeks must be less than project.timeline_weeks")
        return self


class MaterialRequirements(BaseModel):
    cement_bags: float
    steel_kg: float
    sand_cuft: float
    aggregate_cuft: float
    bricks: float


class CostBreakup(BaseModel):
    labor_cost_inr: float
    material_cost_inr: float
    total_cost_inr: float


class WorkforcePhaseAllocation(BaseModel):
    phase: ConstructionPhase
    weeks: int
    manpower: Dict[str, int]


class WeeklyPlanItem(BaseModel):
    week: int
    phase: ConstructionPhase
    key_tasks: List[str]
    required_workers: Dict[str, int]


class CompressionImpact(BaseModel):
    baseline_timeline_weeks: int
    compressed_timeline_weeks: int
    acceleration_factor: float
    additional_labor_cost_inr: float
    additional_workers_percent: float
    compressed_total_cost_inr: float


class LayoutSuggestion(BaseModel):
    floor: int
    approximate_area_sqft: float
    rooms: Dict[str, int]
    notes: List[str]


class EstimationResponse(BaseModel):
    project: InputProject
    material_requirements: MaterialRequirements
    workforce_allocation: List[WorkforcePhaseAllocation]
    phasewise_plan: Dict[ConstructionPhase, Dict[str, float]]
    weekly_schedule: List[WeeklyPlanItem]
    cost: CostBreakup
    compression_impact: Optional[CompressionImpact]
    ai_layout_suggestions: List[LayoutSuggestion]
