"""Тесты корректности реализаций работы 2."""

from __future__ import annotations

import random

from .core import Checker
from .diagnostics import case_detail
from .inspection import calls_global, calls_method

INT_CASES = [
    ("пустой массив", []),
    ("один элемент", [5]),
    ("два элемента по порядку", [1, 2]),
    ("два элемента наоборот", [2, 1]),
    ("уже отсортирован", [1, 2, 3, 4, 5]),
    ("обратно отсортирован", [5, 4, 3, 2, 1]),
    ("повторяющиеся элементы", [3, 1, 2, 3, 2, 1]),
    ("все элементы одинаковые", [7, 7, 7, 7]),
    ("содержит ноль", [0, 5, 0, 3, 1]),
    ("большие значения", [9999, 10, 500, 1000, 1]),
    ("обычный случай", [9, 4, 1, 7, 3, 8, 2]),
]

FLOAT_CASES = [
    ("пустой массив", []),
    ("один элемент", [0.5]),
    ("два элемента наоборот", [0.9, 0.1]),
    ("уже отсортирован", [0.1, 0.2, 0.3]),
    ("повторяющиеся значения", [0.3, 0.1, 0.3, 0.1]),
    ("значения у краёв", [0.0, 0.999, 0.001, 0.5]),
    ("узкая полоса", [0.011, 0.010, 0.012, 0.0105]),
]


class _Probe(int):
    """Целое, считающее сравнения. Используется для проверки досрочного выхода."""

    comparisons = 0

    @classmethod
    def reset(cls) -> None:
        cls.comparisons = 0

    def __gt__(self, other):
        _Probe.comparisons += 1
        return int(self) > int(other)

    def __lt__(self, other):
        _Probe.comparisons += 1
        return int(self) < int(other)

    def __ge__(self, other):
        _Probe.comparisons += 1
        return int(self) >= int(other)

    def __le__(self, other):
        _Probe.comparisons += 1
        return int(self) <= int(other)


def _skipped(func, title: str, probe_args) -> bool:
    """Заготовка вместо реализации: вариант не выбран, тесты пропускаются."""
    try:
        func(*probe_args)
    except NotImplementedError:
        print(f"{title}: вариант не выбран, тесты пропущены")
        return True
    except Exception:  # noqa: BLE001 - реализация есть, но с ошибкой: тестируем
        return False
    return False


def check_sort(sort_func, title: str, floats: bool = False, optional: bool = False, verbose: bool = True):
    """Проверить сортировку на явных случаях и на случайных данных."""
    if optional and _skipped(sort_func, title, ([0.5, 0.1] if floats else [2, 1],)):
        return None
    checker = Checker(title)
    cases = FLOAT_CASES if floats else INT_CASES

    for name, data in cases:
        original = list(data)
        try:
            result = sort_func(list(data))
        except NotImplementedError:
            raise
        except Exception as error:  # noqa: BLE001
            checker.check(name, False, case_detail(original, repr(error), sorted(original)))
            continue
        checker.check(
            name,
            isinstance(result, list) and result == sorted(original),
            case_detail(original, result, sorted(original)),
        )

    rng = random.Random(42)
    failure = None
    for trial in range(100):
        n = rng.randint(0, 80)
        if floats:
            data = [rng.random() for _ in range(n)]
        else:
            data = [rng.randint(0, max(1, 2 * n)) for _ in range(n)]
        try:
            result = sort_func(list(data))
        except Exception as error:  # noqa: BLE001
            failure = f'seed=42, тест={trial}: ' + case_detail(data, repr(error), sorted(data))
            break
        if result != sorted(data):
            failure = f'seed=42, тест={trial}: ' + case_detail(data, result, sorted(data))
            break
    checker.check("100 случайных массивов", failure is None, failure or "")

    checker.check("встроенная sorted не используется", not calls_global(sort_func, "sorted"))
    checker.check("метод list.sort не используется", not calls_method(sort_func, "sort"))
    checker.check("модуль heapq не используется", not calls_global(sort_func, "heapq"))

    if not floats:
        big = [rng.randint(0, 10_000) for _ in range(512)]
        try:
            result = sort_func(list(big))
            checker.check("массив из 512 элементов", result == sorted(big))
        except RecursionError:
            checker.check(
                "массив из 512 элементов",
                False,
                "переполнение стека: рекурсия слишком глубокая",
            )

    checker.report(verbose)
    return checker


def check_early_exit(sort_func, title: str = "Досрочный выход", optional: bool = False, verbose: bool = True):
    """Проверить, что на отсортированном массиве делается один проход."""
    if optional and _skipped(sort_func, title, ([2, 1],)):
        return None
    checker = Checker(title)
    n = 200
    data = [_Probe(value) for value in range(n)]
    _Probe.reset()
    sort_func(list(data))
    comparisons = _Probe.comparisons
    checker.check(
        "на отсортированном массиве из 200 элементов не более одного прохода",
        comparisons <= 2 * n,
        f"сравнений: {comparisons}, у полного перебора было бы около {n * n // 2}",
    )
    checker.report(verbose)
    return checker
