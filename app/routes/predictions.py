from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ml.predict import predict_delay_risk, predict_completion_time, predict_all

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


class PredictionInput(BaseModel):
    """Input schema for prediction endpoints"""
    total_tasks: int
    completed_tasks: int
    delayed_tasks: int
    team_size: int
    completion_pct: int
    task_completion_rate: float
    delayed_task_rate: float


class DelayRiskResponse(BaseModel):
    """Response for delay risk prediction"""
    is_delayed: int
    probability_on_track: float
    probability_delayed: float


class CompletionTimeResponse(BaseModel):
    """Response for completion time prediction"""
    days_remaining: int


class FullPredictionResponse(BaseModel):
    """Response for full prediction"""
    is_delayed: int
    probability_on_track: float
    probability_delayed: float
    days_remaining: int


@router.post("/delay-risk", response_model=DelayRiskResponse)
async def get_delay_risk(data: PredictionInput):
    """
    Predict if a project will be delayed.
    
    Returns:
    - is_delayed: 0 (on track) or 1 (delayed)
    - probability_on_track: confidence of being on track
    - probability_delayed: confidence of being delayed
    """
    try:
        result = predict_delay_risk(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completion-time", response_model=CompletionTimeResponse)
async def get_completion_time(data: PredictionInput):
    """
    Predict days remaining to complete the project.
    
    Returns:
    - days_remaining: estimated days to completion
    """
    try:
        result = predict_completion_time(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-prediction", response_model=FullPredictionResponse)
async def get_full_prediction(data: PredictionInput):
    """
    Get both delay risk and completion time predictions in one call.
    
    Returns:
    - is_delayed: 0 (on track) or 1 (delayed)
    - probability_on_track: confidence of being on track
    - probability_delayed: confidence of being delayed
    - days_remaining: estimated days to completion
    """
    try:
        result = predict_all(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Resource Allocation Endpoint ─────────────────────────────────────────

from app.ml.predict import predict_resource_allocation


class ResourceAllocationInput(BaseModel):
    """Input schema for resource allocation prediction"""
    project_type: int   # 0=web, 1=mobile, 2=ml, 3=devops, 4=embedded
    complexity: int     # 1=low, 2=medium, 3=high
    total_tasks: int
    deadline_days: int
    has_frontend: int   # 0 or 1
    has_backend: int
    has_ml: int
    has_mobile: int
    has_devops: int
    has_database: int


class ResourceAllocationResponse(BaseModel):
    """Response for resource allocation prediction"""
    required_developers: int
    estimated_days: int
    required_skill_sets: list
    project_type_label: str
    complexity_label: str


@router.post("/resource-allocation", response_model=ResourceAllocationResponse)
async def get_resource_allocation(data: ResourceAllocationInput):
    """
    Predict required resources for a new project.

    Returns:
    - required_developers: how many developers are needed
    - estimated_days: estimated project timeline
    - required_skill_sets: list of required skill areas
    - project_type_label: human-readable project type
    - complexity_label: Low / Medium / High
    """
    try:
        result = predict_resource_allocation(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
