from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_hint: str = Field(
        ..., description="Short name/label for the source (e.g., doc title or folder)"
    )
    snippet: str = Field(..., description="Short snippet from KM raw text (<= 40 words)")


class ProposalDraft(BaseModel):
    executive_summary: List[str]
    business_challenges: List[str]
    proposed_solution: List[str]
    architecture_notes: List[str]
    delivery_plan: List[str]
    assumptions: List[str]
    risks: List[str]
    timeline: List[str]
    evidence: List[EvidenceItem]


class PricingLine(BaseModel):
    role: str
    days: float
    rate_per_day: float
    subtotal: float


class PricingPack(BaseModel):
    currency: str
    lines: List[PricingLine]
    overhead_pct: float
    risk_buffer_pct: float
    discount_pct: float
    total_before_discount: float
    total_after_discount: float
    approvals_needed: bool
    approval_reasons: List[str]
    notes: List[str]


class MVPRequest(BaseModel):
    session_id: Optional[str] = None
    scenario: Literal["qualify", "proposal", "pricing"]
    brief: str


class MVPResponse(BaseModel):
    session_id: Optional[str] = None
    scenario: str
    summary: str
    data: dict
