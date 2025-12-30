import os
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from graph import model, settings
from km_verse import fetch_km_knowledge_retrieval
from utils import invoke_strict_json

from .mvp_state import PricingPack, ProposalDraft


def _parse_folders(env_name: str, default: str) -> List[int]:
    raw = os.getenv(env_name, default).strip()
    if not raw:
        return []
    out: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(int(part))
        except ValueError:
            pass
    return out


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def km_retrieve(query: str, folders: List[int]) -> str:
    """
    Reuses the SAME KMVerse retrieval your opportunity agent uses.
    Folder IDs are configurable via env.
    """
    project_id = _get_int("KM_PROJECT_ID", 79)
    kb_id = _get_int("KM_KB_ID", 157674728953541)
    top_k = _get_int("KM_TOP_K", 5)
    score = _get_float("KM_SCORE", 0.2)
    embedding = settings.KM_VERSE_EMBEDDING

    return fetch_km_knowledge_retrieval(
        project_id=project_id,
        knowledge_base_id=kb_id,
        folders=folders,
        embedding=embedding,
        query=query,
        top_k=top_k,
        score=score,
    )


def run_qualify(brief: str) -> Dict[str, Any]:
    """
    Calls your existing BANT-C implementation.
    IMPORTANT: adjust import if your package path differs.
    """
    try:
        # if your project installs src/ as package
        from agent.opportunity_agent import run_bantc_analysis
    except Exception:
        # fallback if needed
        from src.agent.opportunity_agent import run_bantc_analysis  # type: ignore

    analysis = run_bantc_analysis(
        query=brief, extra_user_instruction="overall_summary 用中文即可，其他字段中英皆可。"
    )

    overall = analysis.get("overall_summary") if isinstance(analysis, dict) else str(analysis)
    summary = f"[QUALIFY] Done. Overall summary:\n{overall}"
    return {"summary": summary, "data": analysis}


def run_proposal(brief: str) -> Dict[str, Any]:
    from .mvp_prompts import PROPOSAL_SYS_PROMPT

    folders = _parse_folders("MVP_PROPOSAL_FOLDERS", os.getenv("KM_FOLDERS", ""))
    km_raw = km_retrieve(brief, folders)

    messages = [
        SystemMessage(content=PROPOSAL_SYS_PROMPT),
        HumanMessage(
            content=(
                "Client Brief:\n"
                f"{brief}\n\n"
                "KM Raw Context (use as evidence):\n"
                f"{km_raw}\n\n"
                "Task:\n"
                "Create a proposal draft outline with evidence snippets.\n"
                "Return JSON only."
            )
        ),
    ]

    draft: ProposalDraft = invoke_strict_json(model, messages, ProposalDraft, retry=0)

    # pydantic v2/v1 safe conversion
    try:
        data = draft.model_dump()
    except AttributeError:
        data = draft.dict()

    summary_lines = []
    if data.get("executive_summary"):
        summary_lines.append("• " + "\n• ".join(data["executive_summary"][:6]))
    summary = "[PROPOSAL] Draft ready.\n" + ("\n".join(summary_lines) if summary_lines else "")

    return {"summary": summary, "data": data}


def run_pricing(brief: str) -> Dict[str, Any]:
    from .mvp_prompts import PRICING_SYS_PROMPT

    folders = _parse_folders("MVP_PRICING_FOLDERS", os.getenv("KM_FOLDERS", ""))
    km_raw = km_retrieve(brief, folders)

    messages = [
        SystemMessage(content=PRICING_SYS_PROMPT),
        HumanMessage(
            content=(
                "Client Brief / Scope Notes:\n"
                f"{brief}\n\n"
                "KM Raw Context (rate cards / past pricing examples / rules):\n"
                f"{km_raw}\n\n"
                "Task:\n"
                "Create a simple pricing pack (roles, days, rates, totals) + approval triggers.\n"
                "Return JSON only."
            )
        ),
    ]

    pack: PricingPack = invoke_strict_json(model, messages, PricingPack, retry=0)

    try:
        data = pack.model_dump()
    except AttributeError:
        data = pack.dict()

    total = data.get("total_after_discount", 0)
    approvals = data.get("approvals_needed", False)
    summary = f"[PRICING] Total after discount: {total}. Approvals needed: {approvals}"

    return {"summary": summary, "data": data}


def run_mvp(scenario: str, brief: str) -> Dict[str, Any]:
    if scenario == "qualify":
        return run_qualify(brief)
    if scenario == "proposal":
        return run_proposal(brief)
    if scenario == "pricing":
        return run_pricing(brief)
    raise ValueError(f"Unknown scenario: {scenario}")
