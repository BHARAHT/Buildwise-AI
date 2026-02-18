from fastapi import FastAPI

from .schemas import CostBreakup, EstimationRequest, EstimationResponse
from .services import (
    ai_layout_suggestions,
    allocate_workforce,
    build_weekly_schedule,
    compression_analysis,
    estimate_labor_cost,
    estimate_material_cost,
    estimate_materials,
    phasewise_plan,
)

app = FastAPI(
    title="Buildwise AI Backend",
    description="Backend APIs for residential construction planning and estimation in India",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/estimate", response_model=EstimationResponse)
def generate_estimate(payload: EstimationRequest) -> EstimationResponse:
    project = payload.project
    material_req = estimate_materials(project)
    material_cost = estimate_material_cost(material_req, payload.materials)

    workforce = allocate_workforce(project)
    labor_cost = estimate_labor_cost(workforce, payload.wages)

    total_cost = round(material_cost + labor_cost, 2)
    cost = CostBreakup(
        labor_cost_inr=round(labor_cost, 2),
        material_cost_inr=round(material_cost, 2),
        total_cost_inr=total_cost,
    )

    return EstimationResponse(
        project=project,
        material_requirements=material_req,
        workforce_allocation=workforce,
        phasewise_plan=phasewise_plan(project),
        weekly_schedule=build_weekly_schedule(workforce),
        cost=cost,
        compression_impact=compression_analysis(payload, total_cost, labor_cost),
        ai_layout_suggestions=ai_layout_suggestions(project),
    )
