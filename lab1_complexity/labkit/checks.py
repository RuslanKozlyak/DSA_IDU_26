"""Тесты корректности реализаций работы 1."""

from __future__ import annotations

import random

from .core import Checker
from .diagnostics import case_detail
from .counting import count_accesses, trace_accesses
from .data import random_sorted_case, random_text
from .inspection import is_recursive, uses_loops, uses_slices

LINEAR_CASES = [
    ([], 5),
    ([5], 5),
    ([5], 10),
    ([4, 1, 3, 2], 1),
    ([4, 1, 3, 2], 4),
    ([4, 1, 3, 2], 3),
    ([4, 1, 3, 2], 100),
    ([5, -10, 0, -5], -5),
    ([1, 2, 2, 2, 3], 2),
    ([9, 8, 7, 6, 5, 4, 3, 2, 1, 0], 0),
    ([9, 8, 7, 6, 5, 4, 3, 2, 1, 0], 9),
    ([2, 9, 1, 8, 3, 7, 4, 6, 5, 0], 7),
]

BINARY_CASES = [
    ([], 5),
    ([5], 5),
    ([5], 10),
    ([1, 2, 3, 4], 1),
    ([1, 2, 3, 4], 4),
    ([1, 2, 3, 4], 3),
    ([1, 2, 3, 4], 100),
    ([-10, -5, 0, 5], -5),
    ([1, 2, 2, 2, 3], 2),
    (list(range(1000)), 777),
    (list(range(1000)), -1),
    (list(range(1000)), 1000),
]


def _search_result_ok(array, target, result) -> bool:
    """Корректен ли ответ поиска: индекс любого вхождения либо -1."""
    if target not in array:
        return result == -1
    return isinstance(result, int) and 0 <= result < len(array) and array[result] == target


def check_search(search_func, title: str, expect_logarithmic: bool = False, verbose: bool = True):
    """Проверить реализацию поиска на списке случаев и на случайных данных."""
    checker = Checker(title)

    cases = BINARY_CASES if expect_logarithmic else LINEAR_CASES
    for array, target in cases:
        name = f"массив длины {len(array)}, поиск {target}"
        expected = [i for i, value in enumerate(array) if value == target]
        description = {'любой из индексов': expected} if expected else -1
        inputs = {'arr': array, 'target': target}
        try:
            result = search_func(list(array), target)
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001
            checker.check(name, False, case_detail(inputs, repr(error), description))
            continue
        detail = case_detail(inputs, result, description)
        ok = _search_result_ok(array, target, result)
        checker.check(name, ok, detail if len(array) <= 24 or not ok else '')

    rng = random.Random(42)
    random_ok = True
    failure = ''
    for trial in range(200):
        if expect_logarithmic:
            array, target = random_sorted_case(rng)
        else:
            size = rng.randint(0, 500)
            array = [rng.randint(-100, 100) for _ in range(size)]
            target = rng.randint(-120, 120)
        try:
            result = search_func(list(array), target)
        except Exception as error:  # noqa: BLE001
            random_ok = False
            failure = f'seed=42, тест={trial}: ' + case_detail({'arr': array, 'target': target}, repr(error), 'индекс вхождения или -1')
            break
        if not _search_result_ok(array, target, result):
            random_ok = False
            valid = [i for i, value in enumerate(array) if value == target]
            failure = f'seed=42, тест={trial}: ' + case_detail({'arr': array, 'target': target}, result, valid or -1)
            break
    random_kind = "отсортированных" if expect_logarithmic else "неупорядоченных"
    checker.check(f"200 случайных {random_kind} массивов", random_ok, failure)

    _, accesses = count_accesses(search_func, list(range(1024)), -1)
    if expect_logarithmic:
        _, trace = trace_accesses(search_func, list(range(1024)), -1)
        repeated = sum(a == b for a, b in zip(trace, trace[1:]))
        checker.check(
            "не более одного чтения среднего элемента за шаг",
            0 < len(trace) <= 12 and repeated <= 1,
            f"индексы чтений: {trace!r}",
        )
    else:
        checker.check(
            "просмотрены все элементы при неуспешном поиске в 1024 элементах",
            accesses == 1024,
            f"обращений: {accesses}",
        )

    checker.report(verbose)
    return checker


PALINDROME_CASES = [
    ("", True),
    ("a", True),
    ("aa", True),
    ("ab", False),
    ("aba", True),
    ("abba", True),
    ("abc", False),
    ("level", True),
    ("algorithm", False),
    ("123454321", True),
    ("123456", False),
    ("abcba", True),
    ("abccba", True),
    ("abcdba", False),
]


def check_palindrome(func, verbose: bool = True):
    """Проверить рекурсивную проверку палиндрома, включая запрет циклов и срезов."""
    checker = Checker("Палиндром")

    for text, expected in PALINDROME_CASES:
        checker.check_call(
            "проверка палиндрома",
            func,
            text,
            expected=expected,
            inputs={'text': text},
        )

    rng = random.Random(7)
    random_ok = True
    failure = ''
    for trial in range(300):
        text = random_text(rng)
        expected = text == text[::-1]
        try:
            got = func(text)
        except Exception as error:
            got = repr(error)
        if got is not expected:
            random_ok = False
            failure = f'seed=7, тест={trial}: ' + case_detail({'text': text}, got, expected)
            break
    checker.check("300 случайных строк", random_ok, failure)

    checker.check("циклы не используются", not uses_loops(func))
    checker.check("срезы не используются", not uses_slices(func))
    checker.check("решение рекурсивное", is_recursive(func))

    checker.report(verbose)
    return checker
