"""Provides access to the immutable tab configuration."""

from __future__ import annotations

from typing import Iterable, List

from app.schemas.config import ConfigResponse, TabConfig, TabResponse
from app.services.exceptions import TabNotFound, TabNotRestartable


class ConfigService:
    """Encapsulates the application tab configuration."""

    def __init__(self, tabs: Iterable[TabConfig]):
        self._tabs: tuple[TabConfig, ...] = tuple(tab.model_copy(deep=True) for tab in tabs)
        if not self._tabs:
            raise ValueError("configuration must define at least one tab")

    def tab_count(self) -> int:
        return len(self._tabs)

    def get_tabs(self) -> List[TabConfig]:
        return [tab.model_copy(deep=True) for tab in self._tabs]

    def get_tab(self, idx: int) -> TabConfig:
        try:
            tab = self._tabs[idx]
        except IndexError as exc:
            raise TabNotFound(idx) from exc
        return tab.model_copy(deep=True)

    def assert_restartable(self, idx: int) -> TabConfig:
        tab = self.get_tab(idx)
        if tab.k8s is None:
            raise TabNotRestartable(idx)
        return tab

    def to_response(self) -> ConfigResponse:
        tabs = [
            TabResponse(
                text=tab.text,
                iconUrl=tab.iconUrl,
                iframeUrl=tab.iframeUrl,
                restartable=tab.k8s is not None,
                tabColor=tab.tabColor,
            )
            for tab in self._tabs
        ]
        return ConfigResponse(tabs=tabs)
