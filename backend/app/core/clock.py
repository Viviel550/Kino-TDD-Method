"""Zegar aplikacji. Wszystko, co zależy od czasu (triggery, widoki, serwisy), bierze go stąd,
dzięki czemu testy mogą go przesuwać zamiast czekać."""

from __future__ import annotations

import time
from collections.abc import Callable

Clock = Callable[[], float]  # zwraca unix epoch w sekundach (UTC)


def system_clock() -> float:
    return time.time()


class FakeClock:
    """Zegar do testów: stoi w miejscu, dopóki go nie przesuniesz."""

    def __init__(self, start: float):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds
