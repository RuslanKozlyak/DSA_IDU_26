"""Эксперименты работы 4."""

from __future__ import annotations

import pandas as pd

from .checks import expected_positions
from .core import collect_implemented, measure_time, pick
from .data import (
    SIGNATURES,
    fixed_text_size,
    generate_log,
    hard_case,
    missing_pattern,
    pattern_from_text,
    pattern_sizes,
    random_text,
    text_sizes,
)

PATTERN_LENGTH = 20


def implemented_searches(candidates: dict) -> dict:
    """Оставить только реализованные алгоритмы поиска."""
    return collect_implemented(candidates, lambda func: func("abc", "b"))


def _repeats(n: int) -> int:
    return 5 if n <= 50_000 else 3


def text_length_table(searches: dict) -> pd.DataFrame:
    """Рост длины текста при фиксированной длине образца."""
    rows = []
    for n in text_sizes():
        text = random_text(n, seed=100)
        pattern = pattern_from_text(text, PATTERN_LENGTH)
        for name, func in searches.items():
            rows.append(
                {
                    "Алгоритм": name,
                    "n": n,
                    "m": PATTERN_LENGTH,
                    "Время, с": measure_time(func, text, pattern, repeat_count=_repeats(n)),
                }
            )
    return pd.DataFrame(rows)


def pattern_length_table(searches: dict) -> pd.DataFrame:
    """Рост длины образца при фиксированной длине текста."""
    n = fixed_text_size()
    text = random_text(n, seed=200)
    rows = []
    for m in pattern_sizes():
        pattern = pattern_from_text(text, m)
        for name, func in searches.items():
            rows.append(
                {
                    "Алгоритм": name,
                    "n": n,
                    "m": m,
                    "Время, с": measure_time(func, text, pattern, repeat_count=5),
                }
            )
    return pd.DataFrame(rows)


def found_missing_table(searches: dict) -> pd.DataFrame:
    """Присутствующий и отсутствующий образец на одном и том же тексте."""
    rows = []
    for n in text_sizes():
        text = random_text(n, seed=300)
        cases = {
            "образец есть": pattern_from_text(text, PATTERN_LENGTH),
            "образца нет": missing_pattern(PATTERN_LENGTH),
        }
        for case_name, pattern in cases.items():
            for name, func in searches.items():
                rows.append(
                    {
                        "Случай": case_name,
                        "Алгоритм": name,
                        "n": n,
                        "Время, с": measure_time(func, text, pattern, repeat_count=_repeats(n)),
                    }
                )
    return pd.DataFrame(rows)


def hard_case_table(searches: dict) -> pd.DataFrame:
    """Вырожденный случай: текст из одинаковых символов и почти совпадающий образец."""
    n = pick(20_000, 50_000)
    rows = []
    for m in pattern_sizes():
        text, pattern = hard_case(n, m)
        for name, func in searches.items():
            rows.append(
                {
                    "Алгоритм": name,
                    "n": n,
                    "m": m,
                    "Время, с": measure_time(func, text, pattern, repeat_count=5),
                }
            )
    return pd.DataFrame(rows)


def signature_table(searches: dict, text: str, analyze, signatures=SIGNATURES) -> pd.DataFrame:
    """Разбор сигнатур журнала вашей функцией `analyze`.

    Каждый алгоритм поиска подставляется в неё по очереди; результаты
    сверяются между собой и с эталонными позициями.
    """
    rows = []
    if not searches:
        return pd.DataFrame(columns=["Сигнатура", "Количество", "Первое", "Последнее", "Позиции"])
    for signature in signatures:
        results = {name: analyze(text, signature, func) for name, func in searches.items()}
        values = list(results.values())
        expected = expected_positions(text, signature)
        if any(value["Позиции"] != expected for value in values):
            raise AssertionError(f"неверные позиции сигнатуры {signature!r}")
        if any(value["Позиции"] != values[0]["Позиции"] for value in values):
            raise AssertionError(f"реализации разошлись на сигнатуре {signature!r}")
        row = dict(values[0])
        row["Позиции"] = row["Позиции"][:5] + (["…"] if len(row["Позиции"]) > 5 else [])
        rows.append(row)
    return pd.DataFrame(rows)


def big_log_table(searches: dict, signatures=("ERROR", "WARNING", "database timeout", "cache hit")):
    """Время поиска сигнатур в большом журнале."""
    log = generate_log()
    rows = []
    for signature in signatures:
        for name, func in searches.items():
            rows.append(
                {
                    "Сигнатура": signature,
                    "Алгоритм": name,
                    "Вхождений": len(func(log, signature)),
                    "Время, с": measure_time(func, log, signature, repeat_count=2),
                }
            )
    return pd.DataFrame(rows), log
