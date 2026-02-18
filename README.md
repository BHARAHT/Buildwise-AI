# Buildwise-AI Backend

AI-powered construction planning and estimation backend for **residential projects in India**.

## Tech Stack

- **Python 3.11+**
- **FastAPI** for REST APIs
- **Pydantic v2** for input/output validation
- **Pytest** for API tests

## Features Implemented

- Residential project input (built-up area, floors, timeline)
- Custom wage and material rate configuration
- Automated construction cost estimation (labor + materials)
- Workforce allocation by construction phase
- Material requirement estimation (cement, steel, sand, aggregate, bricks)
- Phase-wise planning
- Week-by-week construction schedule generation
- Timeline compression impact simulation
- AI-style floor layout suggestion engine

## Project Structure

```txt
app/
  main.py         # FastAPI app + route handlers
  schemas.py      # Request/response models
  services.py     # Estimation and planning logic
tests/
  test_estimate_api.py
```

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## API Endpoints

### `GET /health`
Basic health check.

### `POST /api/v1/estimate`
Generate complete planning + estimation output.

Example request:

```json
{
  "project": {
    "built_up_area_sqft": 1800,
    "floors": 2,
    "timeline_weeks": 36
  },
  "wages": {
    "mason_daily_inr": 950,
    "helper_daily_inr": 700,
    "carpenter_daily_inr": 1050,
    "bar_bender_daily_inr": 1050,
    "electrician_daily_inr": 1150,
    "plumber_daily_inr": 1100,
    "painter_daily_inr": 950
  },
  "materials": {
    "cement_bag_inr": 430,
    "steel_kg_inr": 75,
    "sand_cuft_inr": 60,
    "aggregate_cuft_inr": 50,
    "brick_per_piece_inr": 9
  },
  "compression": {
    "target_timeline_weeks": 30
  }
}
```

The response includes:
- `material_requirements`
- `workforce_allocation`
- `phasewise_plan`
- `weekly_schedule`
- `cost`
- `compression_impact`
- `ai_layout_suggestions`

## Run Tests

```bash
pytest -q
```
