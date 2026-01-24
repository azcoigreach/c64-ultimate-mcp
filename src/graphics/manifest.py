"""Manifest generation for graphics outputs."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class Manifest:
    mode: str
    addresses: Dict[str, int]
    output_files: Dict[str, str]
    palette: Dict[str, Any]
    vic_registers: Dict[str, str]
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
