"""Thread-safe status broadcasting for Server-Sent Events."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Dict, Generator, List

from app.schemas.status import StatusPayload, StatusState
from app.services.exceptions import TabNotFound
from app.utils.sse import HeartbeatEvent


@dataclass
class _Subscription:
    queue: "queue.Queue[StatusPayload]"
    active: bool = True


class StatusBroadcaster:
    """Publishes per-tab status updates to multiple subscribers."""

    def __init__(self, tab_count: int):
        self._tab_count = tab_count
        self._lock = threading.Lock()
        self._last: List[StatusPayload] = [
            StatusPayload(state=StatusState.RUNNING) for _ in range(tab_count)
        ]
        self._subscribers: Dict[int, List[_Subscription]] = {i: [] for i in range(tab_count)}

    def _validate_idx(self, idx: int) -> None:
        if idx < 0 or idx >= self._tab_count:
            raise TabNotFound(idx)

    def current(self, idx: int) -> StatusPayload:
        self._validate_idx(idx)
        return self._last[idx]

    def emit(self, idx: int, payload: StatusPayload) -> None:
        """Record and broadcast a new status payload."""
        self._validate_idx(idx)
        with self._lock:
            self._last[idx] = payload
            subscribers = list(self._subscribers[idx])
        for subscriber in subscribers:
            if subscriber.active:
                subscriber.queue.put(payload)

    def listen(
        self,
        idx: int,
        *,
        heartbeat_interval: float | None = None,
    ) -> Generator[StatusPayload | HeartbeatEvent, None, None]:
        """Create a generator that yields status updates (and optional heartbeats)."""
        self._validate_idx(idx)
        subscription = _Subscription(queue.Queue())
        subscription.queue.put(self._last[idx])
        with self._lock:
            self._subscribers[idx].append(subscription)

        heartbeat_value = float(heartbeat_interval) if heartbeat_interval is not None else None
        heartbeat_enabled = heartbeat_value is not None
        timeout = min(1.0, heartbeat_value) if heartbeat_value is not None else 1.0

        def _iterator() -> Generator[StatusPayload | HeartbeatEvent, None, None]:
            last_sent = _now()
            try:
                while subscription.active:
                    try:
                        payload = subscription.queue.get(timeout=timeout)
                    except queue.Empty:
                        if not heartbeat_enabled or not subscription.active:
                            continue
                        now = _now()
                        if heartbeat_value is not None and now - last_sent >= heartbeat_value:
                            last_sent = now
                            yield HeartbeatEvent()
                        continue
                    yield payload
                    last_sent = _now()
            finally:
                subscription.active = False
                with self._lock:
                    try:
                        self._subscribers[idx].remove(subscription)
                    except ValueError:
                        pass
        return _iterator()

    def close_tab(self, idx: int) -> None:
        """Forcefully stop all listeners for the given tab."""
        self._validate_idx(idx)
        with self._lock:
            subscribers = list(self._subscribers[idx])
        for subscriber in subscribers:
            subscriber.active = False
            subscriber.queue.put(self._last[idx])


def _now() -> float:
    """Return the current monotonic time used for heartbeat bookkeeping."""

    return time.perf_counter()
