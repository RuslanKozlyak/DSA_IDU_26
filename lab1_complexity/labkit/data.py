"""Генерация входных данных для работы 1."""

from __future__ import annotations

import random

from .core import pick

# Размеры массивов: быстрый режим и полный режим из условия работы.
FAST_SIZES = [10, 100, 1_000, 10_000]
FULL_SIZES = [10, 100, 1_000, 10_000, 100_000]


def sizes() -> list[int]:
    return list(pick(FAST_SIZES, FULL_SIZES))


def sorted_array(n: int) -> list[int]:
    """Отсортированный массив `0, 1, ..., n-1`."""
    return list(range(n))


def missing_target() -> int:
    """Значение, которого заведомо нет в `sorted_array`: худший случай поиска."""
    return -1


def random_sorted_case(rng: random.Random, max_size: int = 500):
    """Случайный отсортированный массив и случайное искомое значение."""
    n = rng.randint(0, max_size)
    array = sorted(rng.randint(-100, 100) for _ in range(n))
    target = rng.randint(-120, 120)
    return array, target


def random_text(rng: random.Random, max_size: int = 20, alphabet: str = "ab") -> str:
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, max_size)))
