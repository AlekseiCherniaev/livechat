from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domain.entities.outbox import Outbox


class OutboxRepository(Protocol):
    async def save(self, outbox: Outbox, db_session: Any | None = None) -> Outbox: ...

    async def get_by_id(
        self, outbox_id: UUID, db_session: Any | None = None
    ) -> Outbox | None: ...

    async def list_pending(
        self, limit: int, db_session: Any | None = None
    ) -> list[Outbox]: ...

    async def mark_in_progress(
        self, outbox_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def mark_pending(
        self,
        outbox_id: UUID,
        retry: bool = False,
        last_error: str | None = None,
        db_session: Any | None = None,
    ) -> None: ...

    async def mark_sent(
        self, outbox_id: UUID, sent_at: datetime, db_session: Any | None = None
    ) -> None: ...

    async def mark_failed(
        self, outbox_id: UUID, error: str, db_session: Any | None = None
    ) -> None: ...

    async def delete_by_id(
        self, outbox_id: UUID, db_session: Any | None = None
    ) -> None: ...

    async def exists_by_dedup_keys(
        self, dedup_keys: list[str], db_session: Any | None = None
    ) -> list[str]: ...
