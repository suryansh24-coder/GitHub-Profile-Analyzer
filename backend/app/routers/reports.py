from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.reports import export_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ExportRequest(BaseModel):
    format: str = Field(default="json", pattern="^(json|csv|markdown)$")
    title: str = Field(default="Analysis report", max_length=120)
    payload: dict[str, Any]


@router.post("/export")
async def export(payload: ExportRequest) -> dict[str, str]:
    content = export_report({**payload.payload, "generatedAt": datetime.now(timezone.utc).isoformat()}, payload.format, payload.title)
    return content
