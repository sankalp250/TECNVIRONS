import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from .config import get_settings


class SupabaseService:
    """Thin async wrapper around the official Supabase Python client."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "Supabase credentials are missing. Please set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY in your environment."
            )

        self._client: Client = create_client(settings.supabase_url, settings.supabase_key)
        self.schema = settings.supabase_schema

    async def _run(self, func, *args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    async def create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        await self._run(
            lambda: self._client.table("sessions").insert(payload).execute()
        )
        return payload

    async def log_event(
        self,
        session_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        record = {
            "session_id": session_id,
            "event_type": event_type,
            "payload": payload,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._run(
            lambda: self._client.table("session_events").insert(record).execute()
        )

    async def fetch_ordered_events(self, session_id: str) -> List[Dict[str, Any]]:
        def _fetch():
            return (
                self._client.table("session_events")
                .select("*")
                .eq("session_id", session_id)
                .order("occurred_at", desc=False)
                .execute()
            )

        response = await self._run(_fetch)
        return response.data or []

    async def finalize_session(
        self,
        session_id: str,
        summary: str,
        end_time: Optional[datetime] = None,
    ) -> None:
        end_ts = (end_time or datetime.now(timezone.utc)).isoformat()
        await self._run(
            lambda: self._client.table("sessions")
            .update({"summary": summary, "end_time": end_ts, "status": "completed"})
            .eq("session_id", session_id)
            .execute()
        )

