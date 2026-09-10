"""Генерация входных данных для работы 2."""

from __future__ import annotations

import random

from .core import pick

# Общая линейная сетка до 512 для всех алгоритмов. Полный режим увеличивает
# плотность точек, а не максимальный размер. Имена BUBBLE сохранены для API.
FAST_SIZES = list(range(16, 513, 16))
FULL_SIZES = list(range(8, 513, 8))
FAST_BUBBLE_SIZES = FAST_SIZES
FULL_BUBBLE_SIZES = FULL_SIZES


def sizes(bubble: bool = False) -> list[int]:
    if bubble:
        return list(pick(FAST_BUBBLE_SIZES, FULL_BUBBLE_SIZES))
    return list(pick(FAST_SIZES, FULL_SIZES))


def random_ints(n: int, seed: int = 0, high: int | None = None) -> list[int]:
    """Случайные целые из диапазона [0, 2n], если не указано иное."""
    rng = random.Random(seed + n)
    limit = 2 * n if high is None else high
    return [rng.randint(0, limit) for _ in range(n)]


def sorted_ints(n: int, seed: int = 0) -> list[int]:
    return sorted(random_ints(n, seed))


def reversed_ints(n: int, seed: int = 0) -> list[int]:
    return sorted(random_ints(n, seed), reverse=True)


def nearly_sorted_ints(n: int, seed: int = 0, ratio: float = 0.05) -> list[int]:
    """Отсортированный массив, в котором переставлено около `ratio` элементов."""
    data = sorted_ints(n, seed)
    rng = random.Random(seed + 7 * n)
    swaps = int(n * ratio / 2)
    for _ in range(swaps):
        i = rng.randrange(n)
        j = rng.randrange(n)
        data[i], data[j] = data[j], data[i]
    return data


def many_duplicates_ints(n: int, seed: int = 0) -> list[int]:
    """Случайный порядок при узком диапазоне значений: k примерно n / 10."""
    return random_ints(n, seed, high=max(2, n // 10))


def wide_range_ints(n: int, seed: int = 0) -> list[int]:
    """Случайный порядок при широком диапазоне значений: k примерно 100n."""
    return random_ints(n, seed, high=100 * n)


# Наборы различаются двумя признаками сразу: степенью упорядоченности (первые
# четыре) и структурой самих значений (последние два). Сортировки, работа
# которых не зависит от входа, дают одинаковые панели на всех шести наборах.
DATASETS = {
    "случайный": random_ints,
    "отсортированный": sorted_ints,
    "обратный": reversed_ints,
    "почти отсортированный": nearly_sorted_ints,
    "много повторов": many_duplicates_ints,
    "широкий диапазон": wide_range_ints,
}


def ints_with_range(n: int, k: int, seed: int = 0) -> list[int]:
    """Случайные целые из диапазона [0, k): управляет отношением k / n."""
    rng = random.Random(seed + k)
    return [rng.randrange(k) for _ in range(n)]


def ints_with_digits(n: int, digits: int, seed: int = 0) -> list[int]:
    """Случайные целые, записываемые не более чем `digits` десятичными разрядами."""
    rng = random.Random(seed + digits)
    high = 10**digits - 1
    return [rng.randint(0, high) for _ in range(n)]


def uniform_floats(n: int, seed: int = 0) -> list[float]:
    """Равномерное распределение на [0, 1)."""
    rng = random.Random(seed + n)
    return [rng.random() for _ in range(n)]


def concentrated_floats(n: int, seed: int = 0, width: float | None = None) -> list[float]:
    """По умолчанию [0, 1/n): все значения в нулевом из n равных блоков."""
    rng = random.Random(seed + n)
    if width is None:
        width = 1 / max(1, n)
    return [rng.random() * width for _ in range(n)]


DISTRIBUTIONS = {
    "равномерное": uniform_floats,
    "сконцентрированное": concentrated_floats,
}
