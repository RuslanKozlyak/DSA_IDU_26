"""Тесты корректности реализаций работы 4."""

from __future__ import annotations

import random

from .core import Checker
from .diagnostics import case_detail
from .inspection import calls_global, calls_method
from .data import ALPHABET

SEARCH_CASES = [
    ("пустой текст и образец", "", ""),
    ("пустой текст", "", "a"),
    ("пустой образец", "abc", ""),
    ("один символ найден", "a", "a"),
    ("один символ не найден", "a", "b"),
    ("в начале", "abcdef", "abc"),
    ("в середине", "abcdef", "cde"),
    ("в конце", "abcdef", "def"),
    ("образец длиннее текста", "abc", "abcdef"),
    ("несколько вхождений", "abcabcabc", "abc"),
    ("перекрывающиеся вхождения", "ababa", "aba"),
    ("много перекрытий", "aaaaa", "aaa"),
    ("образец равен тексту", "algorithm", "algorithm"),
    ("образца нет", "algorithm", "graph"),
    ("пробелы и знаки", "a b, a b, a b", "a b"),
    ("кириллица", "абракадабра", "абра"),
    ("почти совпадение", "aaaaaaaaab", "aaab"),
]

PREFIX_CASES = [
    ("", []),
    ("a", [0]),
    ("aaaa", [0, 1, 2, 3]),
    ("abcd", [0, 0, 0, 0]),
    ("ababa", [0, 0, 1, 2, 3]),
    ("aabaaab", [0, 1, 0, 1, 2, 2, 3]),
    ("abacabab", [0, 0, 1, 0, 1, 2, 3, 2]),
]


def expected_positions(text: str, pattern: str) -> list[int]:
    """Эталонный ответ: все позиции вхождений, включая перекрывающиеся."""
    if pattern == "":
        return list(range(len(text) + 1))
    positions = []
    start = 0
    while True:
        found = text.find(pattern, start)
        if found == -1:
            return positions
        positions.append(found)
        start = found + 1


def check_search(search_func, title: str, verbose: bool = True):
    """Проверить алгоритм поиска подстроки."""
    checker = Checker(title)

    for name, text, pattern in SEARCH_CASES:
        expected = expected_positions(text, pattern)
        try:
            result = search_func(text, pattern)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001
            checker.check(name, False, case_detail({'text': text, 'pattern': pattern}, repr(error), expected))
            continue
        checker.check(
            name,
            isinstance(result, list) and result == expected,
            case_detail({'text': text, 'pattern': pattern}, result, expected),
        )

    rng = random.Random(42)
    failure = None
    for trial in range(200):
        text = "".join(rng.choice("abc") for _ in range(rng.randint(0, 60)))
        pattern = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))
        try:
            result = search_func(text, pattern)
        except Exception as error:  # noqa: BLE001
            failure = f'seed=42, тест={trial}: ' + case_detail({'text': text, 'pattern': pattern}, repr(error), expected_positions(text, pattern))
            break
        if result != expected_positions(text, pattern):
            failure = f'seed=42, тест={trial}: ' + case_detail({'text': text, 'pattern': pattern}, result, expected_positions(text, pattern))
            break
    checker.check("200 случайных пар «текст, образец»", failure is None, failure or "")

    long_text = "".join(rng.choice(ALPHABET) for _ in range(20_000))
    long_pattern = long_text[9_000:9_030]
    checker.check(
        "текст из 20 000 символов",
        search_func(long_text, long_pattern) == expected_positions(long_text, long_pattern),
    )

    hard_text = "a" * 3_000
    hard_pattern = "a" * 20 + "b"
    checker.check(
        "неблагоприятный случай без вхождений",
        search_func(hard_text, hard_pattern) == [],
    )

    for forbidden in ("find", "index", "rfind", "count", "startswith", "endswith"):
        checker.check(
            f"встроенный поиск подстроки не используется: {forbidden}",
            not calls_method(search_func, forbidden),
        )
    checker.check("модуль re не используется", not calls_global(search_func, "re"))

    checker.report(verbose)
    return checker


def check_prefix_function(prefix_func, verbose: bool = True):
    """Проверить префикс-функцию."""
    checker = Checker("Префикс-функция")

    for pattern, expected in PREFIX_CASES:
        checker.check_call('префикс-функция', prefix_func, pattern, expected=expected, inputs={'pattern': pattern})

    rng = random.Random(3)
    failure = None
    for trial in range(200):
        pattern = "".join(rng.choice("ab") for _ in range(rng.randint(0, 20)))
        expected = []
        for index in range(len(pattern)):
            prefix = pattern[: index + 1]
            best = 0
            for length in range(1, len(prefix)):
                if prefix[:length] == prefix[len(prefix) - length :]:
                    best = length
            expected.append(best)
        try:
            got = prefix_func(pattern)
        except Exception as error:
            got = repr(error)
        if got != expected:
            failure = f'seed=3, тест={trial}: ' + case_detail({'pattern': pattern}, got, expected)
            break
    checker.check("200 случайных образцов", failure is None, failure or "")

    checker.report(verbose)
    return checker


def check_same_results(searches: dict, text: str, patterns: list[str], verbose: bool = True):
    """Проверить, что все реализации дают одинаковый ответ."""
    checker = Checker("Согласованность реализаций")
    for pattern in patterns:
        results = {name: func(text, pattern) for name, func in searches.items()}
        values = list(results.values())
        checker.check(
            f"образец {pattern!r}",
            all(value == values[0] for value in values),
            case_detail({'text': text, 'pattern': pattern}, results, 'одинаковые позиции у всех алгоритмов')
            if len(text) <= 220 or any(value != values[0] for value in values)
            else '',
        )
    checker.report(verbose)
    return checker


def check_signature_analysis(analyze_func, search_func, verbose: bool = True):
    """Проверить разбор сигнатур: позиции, количество, первое и последнее вхождение."""
    checker = Checker("Разбор сигнатур")

    cases = [
        ("INFO start\nERROR timeout\nINFO retry\nERROR timeout", "ERROR"),
        ("aaaa", "aa"),
        ("abcdef", "xyz"),
        ("ERROR", "ERROR"),
        ("", "ERROR"),
    ]
    for text, signature in cases:
        positions = expected_positions(text, signature)
        expected = {
            "Сигнатура": signature,
            "Количество": len(positions),
            "Первое": positions[0] if positions else None,
            "Последнее": positions[-1] if positions else None,
            "Позиции": positions,
        }
        checker.check_call(
            f"сигнатура {signature!r}",
            lambda t=text, s=signature: analyze_func(t, s, search_func),
            expected=expected,
            inputs={'text': text, 'signature': signature},
        )

    checker.report(verbose)
    return checker
