"""Общая инфраструктура практикума: режимы, измерения, отчёты.

Модуль не содержит алгоритмов курса. Всё, что здесь есть, выдаётся студенту
готовым: переключатель размеров эксперимента, измерение времени,
форматирование величин и печать отчёта о тестах.
"""

from __future__ import annotations

import gc
import sys
from time import perf_counter
from contextlib import contextmanager
from timeit import repeat as _timeit_repeat


class Config:
    """Режим эксперимента.

    Быстрый режим подобран так, чтобы весь ноутбук считался за несколько минут.
    Полный режим использует размеры из условия работы.
    """

    def __init__(self) -> None:
        self.full = False

    @property
    def name(self) -> str:
        return "полный" if self.full else "быстрый"


CONFIG = Config()


def use_full_sizes(flag: bool = True) -> None:
    """Включить полные размеры экспериментов."""
    CONFIG.full = bool(flag)
    print(f"Режим экспериментов: {CONFIG.name}")


def pick(fast, full):
    """Выбрать значение по текущему режиму."""
    return full if CONFIG.full else fast


def format_seconds(x: float) -> str:
    if x >= 1:
        return f"{x:.3f} с"
    if x >= 1e-3:
        return f"{x * 1e3:.3f} мс"
    if x >= 1e-6:
        return f"{x * 1e6:.3f} мкс"
    return f"{x * 1e9:.1f} нс"


def _typical(times: list[float]) -> float:
    """Типичное время серии: медиана прогонов без первого.

    Первый прогон отбрасывается как разогревочный: на нём интерпретатор ещё
    не прогрет, а нужные страницы памяти не тронуты, и он систематически
    длиннее остальных. Из оставшихся берётся медиана, а не минимум и не
    среднее: минимум занижает оценку и держится за единственный удачный
    прогон, среднее уводит вверх любой одиночный выброс от посторонней
    нагрузки на машину, а медиана устойчива и к тому, и к другому.
    """
    useful = sorted(times[1:] or times)
    middle = len(useful) // 2
    if len(useful) % 2:
        return useful[middle]
    return (useful[middle - 1] + useful[middle]) / 2


def measure_time(func, *args, repeat_count: int = 5, number: int = 1) -> float:
    """Типичное время одного вызова `func(*args)`."""
    times = _timeit_repeat(lambda: func(*args), repeat=repeat_count, number=number)
    return _typical(times) / number


def measure_time_prepared(make_args, func, repeat_count: int = 5) -> float:
    """Время одного вызова, когда аргументы нужно готовить заново перед каждым.

    Подготовка данных в измерение не входит.
    """
    times = []
    gc.collect()
    for _ in range(repeat_count):
        args = make_args()
        # Сборщик мусора на время замера отключается: его проход по всем
        # созданным объектам иначе попадает в измерение и растёт вместе с n.
        collecting = gc.isenabled()
        gc.disable()
        try:
            start = perf_counter()
            func(*args)
            times.append(perf_counter() - start)
        finally:
            if collecting:
                gc.enable()
    return _typical(times)


@contextmanager
def recursion_limit(limit: int):
    """Временно поднять предел глубины рекурсии.

    Нужен там, где алгоритм намеренно ставится в неудобные условия: например,
    быстрая сортировка с плохим выбором опорного элемента на упорядоченных
    данных уходит на глубину порядка n.
    """
    previous = sys.getrecursionlimit()
    sys.setrecursionlimit(max(previous, limit))
    try:
        yield
    finally:
        sys.setrecursionlimit(previous)


from .diagnostics import Checker


def is_implemented(func, *probe_args) -> bool:
    """Проверить, реализована ли функция (заготовка бросает NotImplementedError)."""
    if func is None:
        return False
    try:
        func(*probe_args)
    except NotImplementedError:
        return False
    except Exception:  # noqa: BLE001 - реализация есть, но пока с ошибкой
        return True
    return True


def collect_implemented(candidates: dict, probe) -> dict:
    """Оставить из словаря `имя -> функция` только реализованные варианты."""
    found = {}
    for name, func in candidates.items():
        if func is None:
            continue
        try:
            probe(func)
        except NotImplementedError:
            continue
        except Exception:  # noqa: BLE001
            found[name] = func
            continue
        found[name] = func
    return found
