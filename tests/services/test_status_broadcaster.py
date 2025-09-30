from __future__ import annotations

from itertools import count

import pytest

import app.services.status_broadcaster as status_broadcaster_module
from app.schemas.status import StatusState
from app.services.status_broadcaster import StatusBroadcaster
from app.utils.sse import HeartbeatEvent


@pytest.mark.parametrize("interval", [0.0015])
def test_listen_emits_heartbeat_when_idle(monkeypatch, interval: float):
    broadcaster = StatusBroadcaster(1)

    ticks = count()
    monkeypatch.setattr(
        status_broadcaster_module,
        "_now",
        lambda: next(ticks) * interval,
    )

    stream = broadcaster.listen(0, heartbeat_interval=interval)
    first = next(stream)
    assert first.state == StatusState.RUNNING

    heartbeat_one = next(stream)
    heartbeat_two = next(stream)

    assert isinstance(heartbeat_one, HeartbeatEvent)
    assert isinstance(heartbeat_two, HeartbeatEvent)

    stream.close()
