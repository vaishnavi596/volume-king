"""Per-authenticated-session, read-only first-data bootstrap accounting.

This state has no credentials, broker order access, or persistent cache.
A last-saved quote never marks a new authenticated generation LOADED.
"""
from dataclasses import dataclass, field

STAGES = ("equities", "indices")
TERMINAL = frozenset(("LOADED", "PARTIAL", "FAILED", "COOLDOWN", "NO AUTH"))

@dataclass
class LoginBootstrapState:
    generation: int | None = None
    stages: dict = field(default_factory=lambda: {key: "NO AUTH" for key in STAGES})
    counts: dict = field(default_factory=dict)

    def begin(self, generation: int, *, authenticated: bool) -> bool:
        """New generation resets proofs; same generation cannot bootstrap twice."""
        if not authenticated:
            self.generation = None
            self.stages = {key: "NO AUTH" for key in STAGES}
            self.counts.clear()
            return False
        if self.generation == generation:
            return False
        self.generation = generation
        self.stages = {key: "LOADING" for key in STAGES}
        self.counts.clear()
        return True

    def finish(self, generation: int, stage: str, received: int, expected: int,
               *, error: str = "") -> bool:
        if generation != self.generation or stage not in STAGES:
            return False
        if not isinstance(received, int) or not isinstance(expected, int) or not (0 <= received <= expected and expected > 0):
            raise ValueError("Invalid bootstrap quote count")
        outcome = ("COOLDOWN" if "429" in error or "cooldown" in error.lower()
                   else "FAILED" if error or not received
                   else "LOADED" if received == expected else "PARTIAL")
        self.stages[stage] = outcome
        self.counts[stage] = (received, expected)
        return True

    def label(self, stage: str) -> str:
        state = self.stages[stage]
        counts = self.counts.get(stage)
        return "Login " + stage + " " + state + (
            f" {counts[0]}/{counts[1]}" if counts else "") + " • Dhan last-known; exchange time unverified"
