"""Воспроизводимые опыты до 512 элементов: сравнения и время."""

from __future__ import annotations

import gc
import random
from statistics import mean, median, quantiles
from time import perf_counter

import pandas as pd

from .core import recursion_limit
from .counting import count_comparisons, count_loop_steps
from .data import sizes, uniform_floats
from .experiments import _progress

RANDOM_INPUT = "Случайный"
KEY_SPACES = (1, 2, 4, 8, 16, 32, 64, 128, 256, 1024, 4096, 65536, 1048576)
COMPARISON_SORTS = {"пузырьковая", "быстрая", "слиянием", "пирамидальная"}
KEY_COLUMNS = ["Эксперимент", "Вариант", "Алгоритм", "n", "x", "Ось x"]
COUNT_COLUMNS = ["Сравнений"]
TIME_COLUMNS = [*KEY_COLUMNS, "Время, с", "Время Q1, с", "Время Q3, с",
                "Входов", "Замеров на вход"]
WORK_COLUMNS = [*KEY_COLUMNS, "Время, с", "Время Q1, с", "Время Q3, с",
                "Работа", "Метрика работы", "Входов", "Замеров на вход"]
RESULT_COLUMNS = [*KEY_COLUMNS, "Время, с", "Время Q1, с", "Время Q3, с",
                  *COUNT_COLUMNS, "Входов", "Замеров на вход"]


def random_input(n, seed, floats=False):
    """Случайная перестановка одного набора значений для всех сортировок."""
    values = uniform_floats(n, seed) if floats else list(range(n))
    random.Random(seed + n).shuffle(values)
    return values


def keyspace_input(n, key_space, seed, floats=False):
    """Случайные ключи из [0, key_space); последний ключ гарантированно встречается."""
    if not isinstance(key_space, int) or key_space < 1:
        raise ValueError("Размер пространства ключей должен быть положительным целым")
    rng = random.Random(seed + n + key_space)
    values = [rng.randrange(key_space) for _ in range(n)] if key_space > 1 else [0] * n
    values[0] = key_space - 1
    return [value / key_space for value in values] if floats else values


def _timings(func, data, repeats):
    """Один прогрев и repeats замеров; копирование и проверка вне таймера."""
    expected = sorted(data)
    readings = []
    collecting = gc.isenabled()
    gc.disable()
    try:
        for run in range(repeats + 1):
            arr = list(data)
            start = perf_counter()
            result = func(arr)
            elapsed = perf_counter() - start
            if result is None or list(result) != expected:
                raise ValueError("Сортировка вернула неверный результат в замере времени")
            if run:
                readings.append(elapsed)
    finally:
        if collecting:
            gc.enable()
    return readings


def _collect(jobs, title, samples, repeats, *, counter="comparisons"):
    if not isinstance(samples, int) or samples < 1:
        raise ValueError("samples должно быть положительным целым")
    if not isinstance(repeats, int) or repeats < 3:
        raise ValueError("repeats должно быть целым не меньше 3")
    expanded = [(f"{meta['Эксперимент']}; {meta['Алгоритм']}; "
                 f"{meta['Вариант']}; {meta['Ось x']}={meta['x']}; вход {sample + 1}/{samples}",
                 meta, func, generator, sample)
                for meta, func, generator in jobs for sample in range(samples)]
    grouped = {}
    gc.collect()
    for meta, func, generator, sample in _progress(expanded, title):
        key = tuple(meta[column] for column in KEY_COLUMNS)
        record = grouped.setdefault(key, {"times": [], "counts": [], "metric": None})
        data = generator(4000 + sample)
        with recursion_limit(4 * len(data) + 1000):
            try:
                # Время нельзя измерять вместе со счётчиками: их методы дороги.
                times = _timings(func, data, repeats)
                if counter == "comparisons":
                    count = count_comparisons(func, data)
                    metric = "Сравнений между элементами"
                elif counter == "by_type":
                    if meta["Алгоритм"] in COMPARISON_SORTS:
                        count = count_comparisons(func, data)
                        metric = "Сравнений между элементами"
                    else:
                        count = count_loop_steps(func, data)
                        metric = "Шагов циклов"
                else:
                    count = metric = None
            except Exception as error:
                raise RuntimeError(f"{meta}; вход {sample + 1}: {error}") from error
        record["times"].extend(times)
        if count is not None:
            record["counts"].append(count)
            record["metric"] = metric
    rows = []
    for key, record in grouped.items():
        q1, _, q3 = quantiles(record["times"], n=4, method="inclusive")
        row = {**dict(zip(KEY_COLUMNS, key)),
               "Время, с": median(record["times"]),
               "Время Q1, с": q1, "Время Q3, с": q3,
               "Входов": samples, "Замеров на вход": repeats}
        if counter == "comparisons":
            row["Сравнений"] = mean(record["counts"])
        elif counter == "by_type":
            row.update({"Работа": mean(record["counts"]),
                        "Метрика работы": record["metric"]})
        rows.append(row)
    columns = {"comparisons": RESULT_COLUMNS, "by_type": WORK_COLUMNS}.get(
        counter, TIME_COLUMNS
    )
    return pd.DataFrame(rows, columns=columns)


def _grid(values):
    points = list(values)
    if not points or any(not isinstance(n, int) or not 2 <= n <= 512 for n in points):
        raise ValueError("Размеры должны быть целыми от 2 до 512")
    return sorted(set(points))


def sorting_table(int_sorts, float_sorts=None, *, grid=None, samples=5, repeats=5):
    """Общее сравнение алгоритмов на случайных входах разного размера."""
    points = _grid(sizes() if grid is None else grid)
    jobs = []
    for sorts, floats in ((int_sorts, False), (float_sorts or {}, True)):
        for name, func in sorts.items():
            for n in points:
                meta = dict(zip(KEY_COLUMNS, ("Размер входа", RANDOM_INPUT, name, n, n, "n")))
                generator = lambda seed, n=n, floats=floats: random_input(n, seed, floats)
                jobs.append((meta, func, generator))
    return _collect(jobs, "Размер входа: все метрики", samples, repeats)


def keyspace_table(int_sorts, float_sorts=None, *, n=512, key_spaces=None,
                   samples=5, repeats=5):
    """Время при фиксированном n и изменении пространства ключей [0, k)."""
    if not isinstance(n, int) or not 2 <= n <= 512:
        raise ValueError("n должен быть целым от 2 до 512")
    points = list(KEY_SPACES if key_spaces is None else key_spaces)
    if not points or any(not isinstance(k, int) or k < 1 for k in points):
        raise ValueError("Размеры пространства ключей должны быть положительными целыми")
    points = sorted(set(points))
    jobs = []
    for sorts, floats in ((int_sorts, False), (float_sorts or {}, True)):
        for name, func in sorts.items():
            for key_space in points:
                meta = dict(zip(KEY_COLUMNS, (
                    "Пространство ключей", f"k = {key_space}", name,
                    n, key_space, "k",
                )))
                generator = lambda seed, key_space=key_space, floats=floats: keyspace_input(
                    n, key_space, seed, floats
                )
                jobs.append((meta, func, generator))
    return _collect(
        jobs, "Пространство ключей: время и работа", samples, repeats,
        counter="by_type",
    )
