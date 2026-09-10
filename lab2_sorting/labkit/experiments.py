"""Эксперименты работы 2."""

from __future__ import annotations

import pandas as pd
from tqdm.auto import tqdm

from .core import (
    collect_implemented,
    measure_time_prepared,
    pick,
    recursion_limit,
)
from .counting import count_accesses, count_comparisons
from .data import (
    DATASETS,
    DISTRIBUTIONS,
    ints_with_digits,
    random_ints,
    sizes,
    uniform_floats,
)

BUBBLE_NAME = "пузырьковая"


def implemented_sorts(candidates: dict, floats: bool = False) -> dict:
    """Оставить только реализованные сортировки: заготовки пропускаются."""
    probe = (lambda func: func([0.5, 0.1])) if floats else (lambda func: func([2, 1]))
    return collect_implemented(candidates, probe)


def _time_of(sort_func, data, repeat_count: int = 3) -> float:
    return measure_time_prepared(lambda: (list(data),), sort_func, repeat_count)


def _progress(jobs, title):
    """Один шаг — один законченный опыт, без обновлений внутри замера."""
    with tqdm(total=len(jobs), desc=title, unit="опыт", dynamic_ncols=True) as bar:
        for label, *args in jobs:
            bar.set_postfix_str(label, refresh=False)
            yield args
            bar.update(1)


def _sort_jobs(int_sorts, float_sorts=None):
    jobs = []
    for sorts, generator in ((int_sorts, random_ints), (float_sorts or {}, uniform_floats)):
        for name, func in sorts.items():
            for n in sizes(bubble=BUBBLE_NAME in name.lower()):
                jobs.append((f"{name}, n={n:,}", name, func, n, generator))
    return jobs


def growth_table(int_sorts: dict, float_sorts: dict | None = None) -> pd.DataFrame:
    """Рост времени работы при увеличении n."""
    rows = []
    for name, sort_func, n, generator in _progress(
            _sort_jobs(int_sorts, float_sorts), "Рост времени"):
        data = generator(n, seed=1000)
        rows.append({"Алгоритм": name, "n": n,
                     "Время, с": _time_of(sort_func, data, repeat_count=5)})
    return pd.DataFrame(rows)


def comparison_table(int_sorts: dict, float_sorts: dict | None = None) -> pd.DataFrame:
    """Число сравнений между элементами при растущем n.

    Величина точная, а не измеренная: она не зависит ни от машины, ни от
    интерпретатора, поэтому классы роста на её графике разделяются, тогда как
    на графике времени постоянные множители сводят их в одну полосу.
    """
    rows = []
    for name, sort_func, n, generator in _progress(
            _sort_jobs(int_sorts, float_sorts), "Число сравнений"):
        data = generator(n, seed=1000)
        with recursion_limit(4 * n + 1000):
            try:
                total = count_comparisons(sort_func, data)
            except RecursionError:
                total = float("nan")
        rows.append({"Алгоритм": name, "n": n, "Сравнений": total})
    return pd.DataFrame(rows)


def dataset_table(int_sorts: dict) -> pd.DataFrame:
    """Сравнение на наборах, различающихся упорядоченностью и структурой значений.

    Прогонов три, а не два: медиана двух измерений есть их среднее, и одиночный
    выброс от посторонней нагрузки на машину смещает результат целиком.
    """
    rows = []
    jobs = []
    for arrangement, generator in DATASETS.items():
        for name, sort_func in int_sorts.items():
            is_bubble = BUBBLE_NAME in name.lower()
            for n in sizes(bubble=is_bubble):
                jobs.append((f"{arrangement}; {name}, n={n:,}",
                             arrangement, name, sort_func, n, generator))
    for arrangement, name, sort_func, n, generator in _progress(jobs, "Разные данные"):
        data = generator(n, seed=2000)
        with recursion_limit(4 * n + 1000):
            try:
                elapsed = _time_of(sort_func, data, repeat_count=3)
            except RecursionError:
                elapsed = float("nan")
            try:
                accesses = count_accesses(sort_func, data)
            except RecursionError:
                accesses = dict.fromkeys(("Чтений", "Записей", "Обращений"), float("nan"))
        rows.append({"Тип данных": arrangement, "Алгоритм": name, "n": n,
                     "Время, с": elapsed, **accesses})
    return pd.DataFrame(rows)


def radix_digits_table(radix_sort) -> pd.DataFrame:
    """Поразрядная сортировка: влияние числа разрядов."""
    n = pick(512, 512)
    rows = []
    jobs = [(f"разрядов={d}, n={n:,}", d) for d in (2, 4, 6, 8)]
    for (digits,) in _progress(jobs, "Число разрядов"):
        data = ints_with_digits(n, digits, seed=6000)
        rows.append(
            {
                "n": n,
                "Разрядов": digits,
                "Время, с": _time_of(radix_sort, data, repeat_count=6),
            }
        )
    return pd.DataFrame(rows)


def bucket_sizes() -> list[int]:
    return list(pick([32, 64, 128, 256, 512], [32, 64, 96, 128, 192, 256, 384, 512]))


def bucket_distribution_table(bucket_sort) -> pd.DataFrame:
    """Блочная сортировка: равномерное и сконцентрированное распределение."""
    rows = []
    jobs = [(f"{name}, n={n:,}", name, generator, n)
            for name, generator in DISTRIBUTIONS.items() for n in bucket_sizes()]
    for distribution, generator, n in _progress(jobs, "Распределения"):
        data = generator(n, seed=7000)
        rows.append({"Распределение": distribution, "n": n,
                     "Время, с": _time_of(bucket_sort, data, repeat_count=6)})
    return pd.DataFrame(rows)
