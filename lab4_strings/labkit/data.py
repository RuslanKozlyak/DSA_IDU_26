"""Генерация текстов, образцов и журналов для работы 4."""

from __future__ import annotations

import random

from .core import pick

# Шаг — удвоение: отношение соседних значений прямо даёт порядок роста
# (2 — линейный, 4 — квадратичный по этому параметру).
FAST_TEXT_SIZES = [2_000, 4_000, 8_000, 16_000, 32_000]
FULL_TEXT_SIZES = [2_000, 4_000, 8_000, 16_000, 32_000, 64_000, 128_000]

FAST_PATTERN_SIZES = [8, 16, 32, 64, 128]
FULL_PATTERN_SIZES = [8, 16, 32, 64, 128, 256, 512]

ALPHABET = "abcd"


def text_sizes() -> list[int]:
    return list(pick(FAST_TEXT_SIZES, FULL_TEXT_SIZES))


def pattern_sizes() -> list[int]:
    return list(pick(FAST_PATTERN_SIZES, FULL_PATTERN_SIZES))


def fixed_text_size() -> int:
    return pick(20_000, 100_000)


def random_text(n: int, seed: int = 0, alphabet: str = ALPHABET) -> str:
    rng = random.Random(seed + n)
    return "".join(rng.choice(alphabet) for _ in range(n))


def pattern_from_text(text: str, length: int) -> str:
    """Образец, который заведомо есть в тексте."""
    start = max(0, len(text) // 2)
    return text[start : start + length]


def missing_pattern(length: int, alphabet: str = ALPHABET) -> str:
    """Образец, которого заведомо нет в тексте из данного алфавита."""
    return "z" * length


def hard_case(n: int, m: int) -> tuple[str, str]:
    """Неблагоприятный случай для наивного поиска.

    Текст из одинаковых символов и образец, отличающийся от них только
    последним символом: наивный алгоритм на каждой позиции сравнивает почти
    весь образец и лишь затем обнаруживает несовпадение.
    """
    return "a" * n, "a" * (m - 1) + "b"


LOG_TEMPLATES = [
    "INFO request completed",
    "INFO user login",
    "INFO cache hit",
    "WARNING high memory usage",
    "WARNING slow request",
    "ERROR database timeout",
    "ERROR connection refused",
    "DEBUG heartbeat",
]

SIGNATURES = [
    "ERROR",
    "WARNING",
    "database timeout",
    "user login",
    "connection refused",
    "CRITICAL",
]

SMALL_LOG = (
    "2026-08-31 10:00:01 INFO service started\n"
    "2026-08-31 10:00:03 INFO user login id=42\n"
    "2026-08-31 10:00:05 WARNING high memory usage\n"
    "2026-08-31 10:00:08 ERROR database timeout\n"
    "2026-08-31 10:00:09 INFO retry database request\n"
    "2026-08-31 10:00:11 ERROR database timeout\n"
    "2026-08-31 10:00:13 WARNING high memory usage\n"
    "2026-08-31 10:00:15 INFO user logout id=42\n"
    "2026-08-31 10:00:18 ERROR connection refused\n"
)


def generate_log(lines: int | None = None, seed: int = 42) -> str:
    """Длинный журнал событий из типовых строк."""
    count = lines if lines is not None else pick(2_000, 10_000)
    rng = random.Random(seed)
    return "".join(f"{index:08d} {rng.choice(LOG_TEMPLATES)}\n" for index in range(count))
