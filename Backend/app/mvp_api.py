from fastapi import APIRouter

from .mvp_engine import run_mvp
from .mvp_state import MVPRequest, MVPResponse

router = APIRouter(prefix="/api/mvp", tags=["mvp"])


@router.post("/run", response_model=MVPResponse)
def mvp_run(req: MVPRequest) -> MVPResponse:
    result = run_mvp(req.scenario, req.brief)
    return MVPResponse(
        session_id=req.session_id,
        scenario=req.scenario,
        summary=result["summary"],
        data=result["data"] if isinstance(result["data"], dict) else {"raw": str(result["data"])},
    )
