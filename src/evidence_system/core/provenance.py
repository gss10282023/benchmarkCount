"""Provenance placeholders for later artifact-backed implementation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProvenancePlaceholder:
    component: str
    status: str = "bootstrap_only"
