from __future__ import annotations

import math
from typing import Dict, List

from .schemas import (
    CompressionImpact,
    ConstructionPhase,
    EstimationRequest,
    InputProject,
    LayoutSuggestion,
    MaterialRequirements,
    MaterialRateConfig,
    WageConfig,
    WeeklyPlanItem,
    WorkforcePhaseAllocation,
)

PHASE_WEIGHTS: Dict[ConstructionPhase, float] = {
    ConstructionPhase.foundation: 0.2,
    ConstructionPhase.structure: 0.35,
    ConstructionPhase.roofing: 0.15,
    ConstructionPhase.finishing: 0.30,
}

PHASE_TASKS: Dict[ConstructionPhase, List[str]] = {
    ConstructionPhase.foundation: ["Excavation", "PCC", "Footings", "Plinth beam"],
    ConstructionPhase.structure: ["Columns", "Beams", "Slab casting", "Masonry"],
    ConstructionPhase.roofing: ["Slab waterproofing", "Parapet", "Roof utilities"],
    ConstructionPhase.finishing: ["Plaster", "Flooring", "Electrical", "Painting", "Fixtures"],
}


def estimate_materials(project: InputProject) -> MaterialRequirements:
    area = project.built_up_area_sqft
    floors_factor = 1 + (project.floors - 1) * 0.08
    return MaterialRequirements(
        cement_bags=area * 0.42 * floors_factor,
        steel_kg=area * 4.1 * floors_factor,
        sand_cuft=area * 1.82 * floors_factor,
        aggregate_cuft=area * 1.5 * floors_factor,
        bricks=area * 8.8 * floors_factor,
    )


def estimate_material_cost(req: MaterialRequirements, rates: MaterialRateConfig) -> float:
    return (
        req.cement_bags * rates.cement_bag_inr
        + req.steel_kg * rates.steel_kg_inr
        + req.sand_cuft * rates.sand_cuft_inr
        + req.aggregate_cuft * rates.aggregate_cuft_inr
        + req.bricks * rates.brick_per_piece_inr
    )


def _base_worker_mix(project: InputProject) -> Dict[str, int]:
    area_factor = max(1, math.ceil(project.built_up_area_sqft / 900))
    return {
        "mason": max(2, area_factor),
        "helper": max(3, area_factor + 1),
        "carpenter": max(1, math.ceil(area_factor * 0.8)),
        "bar_bender": max(1, math.ceil(area_factor * 0.7)),
        "electrician": max(1, math.ceil(project.floors * 0.8)),
        "plumber": max(1, math.ceil(project.floors * 0.6)),
        "painter": max(1, math.ceil(area_factor * 0.9)),
    }


def allocate_workforce(project: InputProject) -> List[WorkforcePhaseAllocation]:
    base = _base_worker_mix(project)
    timeline = project.timeline_weeks

    phase_worker_multiplier = {
        ConstructionPhase.foundation: {"mason": 1.2, "helper": 1.3, "carpenter": 0.9, "bar_bender": 1.1, "electrician": 0.2, "plumber": 0.2, "painter": 0.0},
        ConstructionPhase.structure: {"mason": 1.4, "helper": 1.4, "carpenter": 1.3, "bar_bender": 1.4, "electrician": 0.4, "plumber": 0.4, "painter": 0.0},
        ConstructionPhase.roofing: {"mason": 1.0, "helper": 1.0, "carpenter": 0.8, "bar_bender": 0.8, "electrician": 0.3, "plumber": 0.3, "painter": 0.0},
        ConstructionPhase.finishing: {"mason": 0.8, "helper": 1.0, "carpenter": 1.1, "bar_bender": 0.2, "electrician": 1.2, "plumber": 1.1, "painter": 1.5},
    }

    allocations: List[WorkforcePhaseAllocation] = []
    for phase, weight in PHASE_WEIGHTS.items():
        weeks = max(1, round(timeline * weight))
        manpower = {
            role: max(0, math.ceil(count * phase_worker_multiplier[phase][role]))
            for role, count in base.items()
        }
        allocations.append(WorkforcePhaseAllocation(phase=phase, weeks=weeks, manpower=manpower))

    allocated_weeks = sum(item.weeks for item in allocations)
    diff = timeline - allocated_weeks
    allocations[-1].weeks += diff
    return allocations


def estimate_labor_cost(workforce: List[WorkforcePhaseAllocation], wages: WageConfig) -> float:
    role_rate = {
        "mason": wages.mason_daily_inr,
        "helper": wages.helper_daily_inr,
        "carpenter": wages.carpenter_daily_inr,
        "bar_bender": wages.bar_bender_daily_inr,
        "electrician": wages.electrician_daily_inr,
        "plumber": wages.plumber_daily_inr,
        "painter": wages.painter_daily_inr,
    }

    total = 0.0
    for phase in workforce:
        worker_day_cost = sum(role_rate[role] * count for role, count in phase.manpower.items())
        total += worker_day_cost * 6 * phase.weeks
    return total


def phasewise_plan(project: InputProject) -> Dict[ConstructionPhase, Dict[str, float]]:
    plan: Dict[ConstructionPhase, Dict[str, float]] = {}
    for phase, weight in PHASE_WEIGHTS.items():
        plan[phase] = {
            "duration_weeks": max(1, round(project.timeline_weeks * weight)),
            "completion_percent": round(weight * 100, 2),
        }
    return plan


def build_weekly_schedule(workforce: List[WorkforcePhaseAllocation]) -> List[WeeklyPlanItem]:
    schedule: List[WeeklyPlanItem] = []
    week_number = 1
    for phase_allocation in workforce:
        for _ in range(phase_allocation.weeks):
            schedule.append(
                WeeklyPlanItem(
                    week=week_number,
                    phase=phase_allocation.phase,
                    key_tasks=PHASE_TASKS[phase_allocation.phase],
                    required_workers=phase_allocation.manpower,
                )
            )
            week_number += 1
    return schedule


def compression_analysis(
    request: EstimationRequest,
    baseline_total_cost: float,
    baseline_labor_cost: float,
) -> CompressionImpact | None:
    if not request.compression:
        return None

    base_weeks = request.project.timeline_weeks
    target_weeks = request.compression.target_timeline_weeks
    acceleration_factor = round(base_weeks / target_weeks, 2)

    added_workers_percent = (acceleration_factor - 1) * 60
    extra_labor = baseline_labor_cost * (added_workers_percent / 100)

    return CompressionImpact(
        baseline_timeline_weeks=base_weeks,
        compressed_timeline_weeks=target_weeks,
        acceleration_factor=acceleration_factor,
        additional_labor_cost_inr=round(extra_labor, 2),
        additional_workers_percent=round(added_workers_percent, 2),
        compressed_total_cost_inr=round(baseline_total_cost + extra_labor, 2),
    )


def ai_layout_suggestions(project: InputProject) -> List[LayoutSuggestion]:
    per_floor = project.built_up_area_sqft / project.floors
    suggestions: List[LayoutSuggestion] = []
    for floor in range(1, project.floors + 1):
        if per_floor <= 700:
            rooms = {"bedroom": 1, "bathroom": 1, "kitchen": 1, "living": 1}
            notes = ["Compact planning with multipurpose spaces", "Prefer open kitchen + dining"]
        elif per_floor <= 1200:
            rooms = {"bedroom": 2, "bathroom": 2, "kitchen": 1, "living": 1, "balcony": 1}
            notes = ["Suitable for nuclear family", "Allocate utility area near kitchen"]
        else:
            rooms = {"bedroom": 3, "bathroom": 3, "kitchen": 1, "living": 1, "dining": 1, "balcony": 2}
            notes = ["Include ventilation shafts for tropical climate", "Use vastu-aligned orientation where applicable"]

        if floor == 1:
            notes.append("Reserve front setback for parking or garden")
        suggestions.append(LayoutSuggestion(floor=floor, approximate_area_sqft=round(per_floor, 2), rooms=rooms, notes=notes))

    return suggestions
