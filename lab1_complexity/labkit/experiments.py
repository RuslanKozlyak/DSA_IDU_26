"""Эксперименты работы 1: число обращений и время работы."""

from __future__ import annotations

import pandas as pd

from .core import measure_time, pick
from .counting import count_accesses
from .data import missing_target, sizes, sorted_array


def accesses_table(searches: dict) -> pd.DataFrame:
    """Число обращений к элементам массива при неуспешном поиске (худший случай)."""
    rows = []
    for n in sizes():
        array = sorted_array(n)
        target = missing_target()
        row = {"n": n}
        for name, func in searches.items():
            _, accesses = count_accesses(func, array, target)
            row[name] = accesses
        rows.append(row)
    return pd.DataFrame(rows)


def _repeats_for(n: int, logarithmic: bool) -> int:
    if logarithmic:
        return 2_000
    if n <= 1_000:
        return 500
    if n <= 10_000:
        return 100
    return pick(5, 20)


def time_table(searches: dict, logarithmic: set[str] = frozenset()) -> pd.DataFrame:
    """Время одного поиска при неуспешном поиске."""
    rows = []
    for n in sizes():
        array = sorted_array(n)
        target = missing_target()
        row = {"n": n}
        for name, func in searches.items():
            number = _repeats_for(n, name in logarithmic)
            row[name] = measure_time(func, array, target, repeat_count=5,
                                     number=number)
        rows.append(row)
    return pd.DataFrame(rows)
