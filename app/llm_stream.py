from __future__ import annotations
from typing import AsyncIterator, List
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq

from .config import get_settings


class GroqStreamer:
    """Wrapper around ChatGroq that exposes async token streaming."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY environment variable.")
        self._llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.7,
            max_tokens=None,
            streaming=True,
        )

    @property
    def client(self) -> ChatGroq:
        return self._llm

    async def stream(self, messages: List[BaseMessage]) -> AsyncIterator[str]:
        async for chunk in self._llm.astream(messages):
            if hasattr(chunk, "content"):
                yield chunk.content or ""

