"""Provider-neutral, ordered facts about an extraction job's execution."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProcessingEvent:
    phase: str
    action: str
    status: str = "completed"
    details: dict = field(default_factory=dict)
