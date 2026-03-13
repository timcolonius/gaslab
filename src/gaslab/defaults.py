from dataclasses import dataclass


@dataclass
class Defaults:
    small: float = 1e-6
    linewidth: float = 2.0
    fontsize: int = 12
    machrange: tuple = (0.01, 10.0)
    color: tuple = ("b", "r", "g", "k")
