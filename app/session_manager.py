from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .config import get_settings
from .langgraph_flow import ConversationOrchestrator
from .llm_stream import GroqStreamer
from .supabase_client import SupabaseService


class SessionRuntime:
    """In-memory container storing per-session conversation state."""

    def __init__(self, session_id: str, user_id: str, system_prompt: str):
        self.session_id = session_id
        self.user_id = user_id
        self.messages: List = [SystemMessage(content=system_prompt)]
        self.started_at = datetime.now(timezone.utc)

    def append_user(self, content: str) -> None:
        self.messages.append(HumanMessage(content=content, name=self.user_id))

    def append_ai(self, content: str) -> None:
        self.messages.append(AIMessage(content=content, name="zephyr"))


class SessionManager:
    """Coordinates Supabase persistence, LangGraph orchestration, and Groq streaming."""

    def __init__(self) -> None:
        settings = get_settings()
        self._supabase = SupabaseService()
        self._streamer = GroqStreamer()
        self._orchestrator = ConversationOrchestrator(system_prompt=settings.system_prompt)
        self._sessions: Dict[str, SessionRuntime] = {}
        self._summary_llm = GroqStreamer()  # reuse config

    async def start(self, session_id: str, user_id: str) -> SessionRuntime:
        runtime = SessionRuntime(session_id, user_id, get_settings().system_prompt)
        await self._supabase.create_session(session_id, user_id)
        self._sessions[session_id] = runtime
        return runtime

    def get_runtime(self, session_id: str) -> SessionRuntime:
        return self._sessions[session_id]

    async def handle_user_turn(
        self, session_id: str, user_payload: str
    ) -> asyncio.Queue[str]:
        runtime = self.get_runtime(session_id)
        runtime.append_user(user_payload)
        await self._supabase.log_event(
            session_id, "user_message", {"content": user_payload, "user_id": runtime.user_id}
        )

        messages_for_llm = await self._orchestrator.run_turn(runtime.messages[1:])

        stream_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _stream():
            buffer = []
            async for token in self._streamer.stream(messages_for_llm):
                buffer.append(token)
                await stream_queue.put(token)
            full_response = "".join(buffer)
            runtime.append_ai(full_response)
            await self._supabase.log_event(
                session_id, "ai_message", {"content": full_response, "model": get_settings().groq_model}
            )
            await stream_queue.put("__END__")

        asyncio.create_task(_stream())
        return stream_queue

    async def summarize_and_finalize(self, session_id: str) -> None:
        events = await self._supabase.fetch_ordered_events(session_id)
        transcript = "\n".join(
            f"[{event['event_type']}] {event['payload'].get('content')}"
            for event in events
            if event.get("payload")
        )
        messages = [
            SystemMessage(
                content=(
                    "You are a meeting summarizer. Produce a 5 sentence recap with "
                    "bulletable highlights and action items when possible."
                )
            ),
            HumanMessage(
                content=f"Conversation transcript:\n{transcript}\nSummarize key insights."
            ),
        ]

        summary_chunks = []
        async for chunk in self._summary_llm.stream(messages):
            summary_chunks.append(chunk)
        summary = "".join(summary_chunks)
        await self._supabase.finalize_session(session_id, summary)
        self._sessions.pop(session_id, None)

