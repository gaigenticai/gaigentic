"""Seed default templates."""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from backend.gaigentic_backend.database import SessionLocal
from backend.gaigentic_backend.models.template import Template

TEMPLATES = [
    (
        "Cash Forecasting Agent",
        "Forecast cash flow based on transaction history",
        {
            "nodes": [
                {"id": "start", "type": "start", "label": "Start", "data": {}, "position": {"x": 0, "y": 0}},
                {"id": "forecast", "type": "forecast", "label": "Forecast", "data": {}, "position": {"x": 200, "y": 0}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "forecast"},
            ],
        },
        "You are a cash forecasting assistant.",
    ),
    (
        "KYC Verification Flow",
        "Verify customer identity using provided documents",
        {
            "nodes": [
                {"id": "input", "type": "input", "label": "Receive Docs", "data": {}, "position": {"x": 0, "y": 0}},
                {"id": "check", "type": "kyc_check", "label": "Verify", "data": {}, "position": {"x": 200, "y": 0}},
            ],
            "edges": [
                {"id": "e2", "source": "input", "target": "check"},
            ],
        },
        "Ensure the documents meet compliance standards.",
    ),
    (
        "Fraud Detection Assistant",
        "Analyze transactions for fraudulent patterns",
        {
            "nodes": [
                {"id": "src", "type": "source", "label": "Transactions", "data": {}, "position": {"x": 0, "y": 0}},
                {"id": "detect", "type": "fraud", "label": "Detect", "data": {}, "position": {"x": 200, "y": 0}},
            ],
            "edges": [
                {"id": "e3", "source": "src", "target": "detect"},
            ],
        },
        "Flag suspicious activities.",
    ),
]


async def main() -> None:
    async with SessionLocal() as session:
        for name, desc, draft, prompt in TEMPLATES:
            result = await session.execute(select(Template.id).where(Template.name == name))
            exists = result.scalar_one_or_none()
            if exists:
                continue
            session.add(
                Template(
                    name=name,
                    description=desc,
                    workflow_draft=draft,
                    system_prompt=prompt,
                    created_by="seed",
                )
            )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
