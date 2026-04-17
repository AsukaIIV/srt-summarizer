from dataclasses import dataclass


@dataclass
class LayoutMode:
    compact: bool = False


@dataclass
class RunStats:
    success: int = 0
    failed: int = 0
