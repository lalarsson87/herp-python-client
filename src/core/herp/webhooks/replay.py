"""
Webhook Event Replay Mechanism

Provides persistent storage and replay of webhook events for debugging,
disaster recovery, and event reprocessing.

Features:
- Persistent event storage (JSON file-based)
- Bulk event replay with filtering
- Event search and query capabilities
- Replay analytics and reporting
- Event deduplication
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

from ...utils.logging import get_logger
from .router import FailedEvent, WebhookRouter

logger = get_logger(__name__)


class EventStore:
    """
    Persistent storage for webhook events

    Stores webhook events to disk for replay and analysis.
    Uses JSON Lines format for efficient append-only storage.
    """

    def __init__(self, storage_path: str = "./.webhook_events"):
        """
        Initialize event store

        Args:
            storage_path: Path to event storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.events_file = self.storage_path / "events.jsonl"
        self.failed_events_file = self.storage_path / "failed_events.jsonl"

        logger.info(f"Event store initialized at {self.storage_path}")

    def store_event(
        self, event_type: str, payload: Dict[str, Any], status: str = "success"
    ) -> None:
        """
        Store webhook event

        Args:
            event_type: Event type
            payload: Event payload
            status: Event processing status ("success", "failed", "retrying")
        """
        event_record = {
            "stored_at": datetime.now().isoformat(),
            "event_type": event_type,
            "event_id": payload.get("event_id"),
            "payload": payload,
            "status": status,
        }

        # Store to appropriate file
        target_file = (
            self.failed_events_file if status == "failed" else self.events_file
        )

        with open(target_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_record, ensure_ascii=False) + "\n")

        logger.debug(f"Stored event {event_type} (status={status})")

    def store_failed_event(self, failed_event: FailedEvent) -> None:
        """
        Store failed event with error details

        Args:
            failed_event: Failed event from dead letter queue
        """
        event_record = {
            "stored_at": datetime.now().isoformat(),
            "event_type": failed_event.payload.get("event"),
            "event_id": failed_event.payload.get("event_id"),
            "payload": failed_event.payload,
            "status": "failed",
            "error": failed_event.error,
            "failed_at": failed_event.failed_at.isoformat(),
            "retries": failed_event.retries,
        }

        with open(self.failed_events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_record, ensure_ascii=False) + "\n")

        logger.debug(f"Stored failed event {event_record['event_id']}")

    def get_events(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query stored events

        Args:
            event_type: Filter by event type
            since: Filter events after this datetime
            until: Filter events before this datetime
            status: Filter by status ("success", "failed")
            limit: Maximum number of events to return

        Returns:
            List of matching event records
        """
        events = []

        # Read from both files
        files_to_read = [self.events_file]
        if status is None or status == "failed":
            files_to_read.append(self.failed_events_file)

        for file_path in files_to_read:
            if not file_path.exists():
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event_record = json.loads(line)

                        # Apply filters
                        if event_type and event_record.get("event_type") != event_type:
                            continue

                        if status and event_record.get("status") != status:
                            continue

                        stored_at = datetime.fromisoformat(event_record["stored_at"])
                        if since and stored_at < since:
                            continue

                        if until and stored_at > until:
                            continue

                        events.append(event_record)

                        # Check limit
                        if limit and len(events) >= limit:
                            return events

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse event record: {e}")

        return events

    def get_failed_events(
        self, since: Optional[datetime] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get failed events

        Args:
            since: Filter events after this datetime
            limit: Maximum number of events

        Returns:
            List of failed event records
        """
        return self.get_events(status="failed", since=since, limit=limit)

    def stream_events(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream events (memory efficient)

        Args:
            event_type: Filter by event type
            since: Filter events after this datetime

        Yields:
            Event records
        """
        for file_path in [self.events_file, self.failed_events_file]:
            if not file_path.exists():
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event_record = json.loads(line)

                        # Apply filters
                        if event_type and event_record.get("event_type") != event_type:
                            continue

                        if since:
                            stored_at = datetime.fromisoformat(
                                event_record["stored_at"]
                            )
                            if stored_at < since:
                                continue

                        yield event_record

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Failed to parse event record: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event storage statistics

        Returns:
            Dictionary with stats
        """
        total_events = 0
        failed_events = 0

        if self.events_file.exists():
            with open(self.events_file, "r") as f:
                total_events = sum(1 for _ in f)

        if self.failed_events_file.exists():
            with open(self.failed_events_file, "r") as f:
                failed_events = sum(1 for _ in f)

        return {
            "total_events": total_events,
            "failed_events": failed_events,
            "storage_path": str(self.storage_path),
        }

    def clear(self, clear_failed: bool = True) -> None:
        """
        Clear stored events

        Args:
            clear_failed: Also clear failed events
        """
        if self.events_file.exists():
            self.events_file.unlink()

        if clear_failed and self.failed_events_file.exists():
            self.failed_events_file.unlink()

        logger.info("Cleared event store")


class EventReplayer:
    """
    Replay webhook events with filtering and reporting

    Replays stored webhook events through a WebhookRouter for debugging,
    testing, and disaster recovery scenarios.

    Usage:
        replayer = EventReplayer(router, event_store)

        # Replay all failed events
        result = replayer.replay_failed_events()
        print(f"Replayed {result['successful']} events")

        # Replay specific event type from last 24 hours
        result = replayer.replay_events(
            event_type="candidacy.created",
            since=datetime.now() - timedelta(days=1)
        )
    """

    def __init__(self, router: WebhookRouter, event_store: EventStore):
        """
        Initialize event replayer

        Args:
            router: WebhookRouter for replaying events
            event_store: EventStore with stored events
        """
        self.router = router
        self.event_store = event_store

    def replay_events(
        self,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Replay stored events

        Args:
            event_type: Filter by event type
            since: Replay events after this datetime
            until: Replay events before this datetime
            status: Filter by status ("success", "failed")
            limit: Maximum number of events to replay
            dry_run: If True, don't actually replay, just count

        Returns:
            Replay statistics
        """
        events = self.event_store.get_events(
            event_type=event_type,
            since=since,
            until=until,
            status=status,
            limit=limit,
        )

        logger.info(
            f"Replaying {len(events)} events "
            f"(event_type={event_type}, dry_run={dry_run})"
        )

        successful = 0
        failed = 0
        skipped = 0

        for event_record in events:
            payload = event_record["payload"]
            event_id = payload.get("event_id")

            if dry_run:
                logger.debug(f"[DRY RUN] Would replay event {event_id}")
                skipped += 1
                continue

            try:
                # Replay through router
                self.router.route(payload)
                successful += 1
                logger.debug(f"Successfully replayed event {event_id}")

            except Exception as e:
                failed += 1
                logger.error(f"Failed to replay event {event_id}: {e}", exc_info=True)

        result = {
            "total": len(events),
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "dry_run": dry_run,
        }

        logger.info(f"Replay completed: {result}")
        return result

    def replay_failed_events(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Replay only failed events

        Args:
            since: Replay events after this datetime
            limit: Maximum number of events to replay
            dry_run: If True, don't actually replay

        Returns:
            Replay statistics
        """
        return self.replay_events(
            status="failed", since=since, limit=limit, dry_run=dry_run
        )

    def replay_event_by_id(self, event_id: str, dry_run: bool = False) -> bool:
        """
        Replay specific event by ID

        Args:
            event_id: Event ID to replay
            dry_run: If True, don't actually replay

        Returns:
            True if event was found and replayed successfully
        """
        # Search for event
        for event_record in self.event_store.stream_events():
            if event_record["event_id"] == event_id:
                if dry_run:
                    logger.info(f"[DRY RUN] Would replay event {event_id}")
                    return True

                try:
                    self.router.route(event_record["payload"])
                    logger.info(f"Successfully replayed event {event_id}")
                    return True
                except Exception as e:
                    logger.error(
                        f"Failed to replay event {event_id}: {e}", exc_info=True
                    )
                    return False

        logger.warning(f"Event {event_id} not found in storage")
        return False

    def replay_with_filter(
        self,
        filter_func: Callable[[Dict[str, Any]], bool],
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Replay events matching custom filter

        Args:
            filter_func: Function to filter events (receives event_record)
            limit: Maximum number of events to replay
            dry_run: If True, don't actually replay

        Returns:
            Replay statistics

        Example:
            >>> # Replay events for specific candidacy
            >>> replayer.replay_with_filter(
            ...     lambda e: e["payload"].get("data", {}).get("candidacy_id") == "cand_123"
            ... )
        """
        successful = 0
        failed = 0
        skipped = 0
        total = 0

        for event_record in self.event_store.stream_events():
            # Apply filter
            if not filter_func(event_record):
                continue

            total += 1
            event_id = event_record["event_id"]

            if dry_run:
                logger.debug(f"[DRY RUN] Would replay event {event_id}")
                skipped += 1
            else:
                try:
                    self.router.route(event_record["payload"])
                    successful += 1
                    logger.debug(f"Successfully replayed event {event_id}")
                except Exception as e:
                    failed += 1
                    logger.error(
                        f"Failed to replay event {event_id}: {e}", exc_info=True
                    )

            # Check limit
            if limit and total >= limit:
                break

        result = {
            "total": total,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "dry_run": dry_run,
        }

        logger.info(f"Filter replay completed: {result}")
        return result

    def get_replay_stats(self) -> Dict[str, Any]:
        """
        Get statistics about replayable events

        Returns:
            Dictionary with stats
        """
        storage_stats = self.event_store.get_stats()
        router_stats = self.router.get_stats()

        return {
            "storage": storage_stats,
            "router": router_stats,
            "replayable_events": storage_stats["total_events"],
            "failed_in_storage": storage_stats["failed_events"],
            "failed_in_dlq": router_stats["dlq_size"],
        }
