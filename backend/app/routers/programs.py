from __future__ import annotations

from fastapi import APIRouter, Query

from ..services.programs import list_programs, VALID_STATUSES

router = APIRouter(prefix="/api/programs", tags=["open-source-programs"])


@router.get("")
async def get_programs(
    status: str | None = None,
    search: str | None = None,
    beginnerFriendly: bool | None = None,
    mentorship: bool | None = None,
    technology: str | None = None,
    upcomingDays: int | None = Query(default=None, ge=0, le=365),
) -> dict[str, object]:
    if status and status not in VALID_STATUSES:
        return {"error": {"code": "invalid_status", "message": f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}"}}
    programs = list_programs(
        status=status,
        search=search,
        beginner_friendly=beginnerFriendly,
        mentorship=mentorship,
        technology=technology,
        upcoming_days=upcomingDays,
    )
    return {
        "items": programs,
        "total": len(programs),
        "statuses": sorted(VALID_STATUSES),
        "verificationNote": "Program data is checked against official sources. Missing dates are shown as null rather than invented. Always confirm on the official site before applying.",
    }
