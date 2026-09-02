"""Common panel interfaces and factory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping

from PIL import Image


@dataclass(frozen=True)
class DisplayConfig:
    width: int = 400
    height: int = 300
    rotation: int = 0


@dataclass(frozen=True)
class PanelMetadata:
    panel_type: str
    display_name: str
    description: str


class BasePanel(ABC):
    @abstractmethod
    def validate(self, data: Mapping[str, Any]) -> Any:
        """Validate raw panel data."""

    @abstractmethod
    def normalize(self, data: Mapping[str, Any]) -> Any:
        """Normalize raw data into an internal render payload."""

    @abstractmethod
    def render(
        self,
        data: Mapping[str, Any],
        config: DisplayConfig,
        preview_mode: str = "normal",
    ) -> Image.Image:
        """Render a panel image."""

    @abstractmethod
    def get_metadata(self) -> PanelMetadata:
        """Describe this panel implementation."""


def create_panel(panel_type: str) -> BasePanel:
    if panel_type == "progress":
        from panels.progress import ProgressPanel

        return ProgressPanel()
    if panel_type == "stats":
        from panels.stats import StatsPanel

        return StatsPanel()
    if panel_type == "flow":
        from panels.flow import FlowPanel

        return FlowPanel()
    raise ValueError(f"Unknown panel type: {panel_type}")
