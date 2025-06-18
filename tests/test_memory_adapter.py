import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from types import SimpleNamespace
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SUPERAGENT_URL", "http://localhost")
os.environ.setdefault("JWT_SECRET_KEY", "test")
os.environ.setdefault("LLM_PROVIDERS_ENABLED", '["openai"]')
os.environ.setdefault("APP_ENV", "test")

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from gaigentic_backend.services import memory_adapter as ma


class FakeResult:
    def __init__(self, data):
        self._data = data

    def all(self):
        return self._data


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.agent = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
        now = datetime.utcnow()
        self.chat_rows = [
            {
                "role": "user",
                "content": "hello",
                "created_at": now - timedelta(minutes=2),
            },
            {
                "role": "assistant",
                "content": "hi there",
                "created_at": now - timedelta(minutes=1),
            },
        ]
        self.kc_rows = [
            SimpleNamespace(content="accounting rules", created_at=now - timedelta(days=1))
        ]
        self.sim_rows = [
            {
                "role": "assistant",
                "content": "remember this",
                "created_at": now - timedelta(minutes=5),
            }
        ]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def execute(self, stmt):
        sql = str(stmt)
        if "knowledge_chunk" in sql:
            return FakeResult(self.kc_rows)
        if "cosine_distance" in sql or "<=>" in sql:
            return FakeResult(self.sim_rows)
        return FakeResult(self.chat_rows)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        pass

    async def get(self, model, pk):
        return self.agent

    def add(self, obj):
        self.added.append(obj)


def test_store_message(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(ma, "SessionLocal", lambda: session)

    async def fake_embed(text):
        return [0.0] * 1536

    monkeypatch.setattr(ma, "get_embedding", fake_embed)

    asyncio.run(ma.store_message(session.agent.id, "user", "hello"))
    assert session.added, "message not added"
    assert session.committed


def test_fetch_context_for_agent(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(ma, "SessionLocal", lambda: session)

    async def fake_embed(text):
        return [0.0] * 1536

    monkeypatch.setattr(ma, "get_embedding", fake_embed)

    result = asyncio.run(ma.fetch_context_for_agent(session.agent.id, "hello"))
    assert isinstance(result, list)
    assert any(r["role"] == "user" for r in result)
    assert any(r["content"] == "remember this" for r in result)
