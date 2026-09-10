"""Эксперименты работы 3."""

from __future__ import annotations

import gc
import random
from time import perf_counter

import pandas as pd
import numpy as np
from tqdm.auto import tqdm

from .core import pick
from .data import KEY_SETS, LOAD_FACTORS, hash_capacity, sizes


def implemented(candidates: dict, probe) -> dict:
    """Оставить реализованные варианты структур: заготовки пропускаются."""
    found = {}
    for name, item in candidates.items():
        try:
            probe(item)
        except NotImplementedError:
            continue
        except Exception:  # noqa: BLE001 - реализация есть, пусть и с ошибкой
            found[name] = item
            continue
        found[name] = item
    return found


def _batch(build, operation, max_count: int) -> int:
    """Размер пачки, при котором замер выходит за грань точности таймера."""
    count = 4
    while count < max_count:
        structure = build()
        start = perf_counter()
        for _ in range(count):
            operation(structure)
        if perf_counter() - start >= 2e-3:
            break
        count = min(max_count, count * 8)
    return count


def _typical(times: list[float]) -> float:
    """Типичное время серии: медиана прогонов без первого.

    Первый прогон отбрасывается как разогревочный. Из оставшихся берётся
    медиана, а не среднее: одиночный выброс от посторонней нагрузки на машину
    среднее уводит вверх, а медиану — нет.
    """
    useful = sorted(times[1:] or times)
    middle = len(useful) // 2
    if len(useful) % 2:
        return useful[middle]
    return (useful[middle - 1] + useful[middle]) / 2


def per_operation_time(build, operation, max_count: int,
                       repeat_count: int = 5) -> float:
    """Типичное время одной операции.

    Одна операция над структурой длится микросекунды, а это на грани точности
    таймера. Поэтому операция повторяется пачкой, а время делится на её размер.
    Пачка прогоняется несколько раз, и из прогонов берётся медиана: одиночный
    замер на этих величинах шумит настолько, что отношения соседних размеров
    перестают что-либо означать. Структура строится заново перед каждым
    прогоном, построение в измерение не входит.
    """
    count = _batch(build, operation, max_count)
    times = []
    for _ in range(repeat_count + 1):
        structure = build()
        # Сборщик мусора на время замера отключается: иначе его проходы по всем
        # созданным узлам попадают в измерение операции и растут вместе с n.
        gc.collect()
        collecting = gc.isenabled()
        gc.disable()
        try:
            start = perf_counter()
            for _ in range(count):
                operation(structure)
            times.append((perf_counter() - start) / count)
        finally:
            if collecting:
                gc.enable()
    return _typical(times)


def operation_time_stats(build, operation, max_count, repeat_count=7):
    """Median and quartiles of batched, uninstrumented operation timings."""
    count = _batch(build, operation, max_count)
    times = []
    for repeat in range(repeat_count + 1):
        structure = build()
        # Do not force a full collection here: it clears Python free lists and
        # makes each short batch artificially cold. Automatic GC is disabled
        # only during the measurement, as in the standalone preview.
        collecting = gc.isenabled()
        gc.disable()
        try:
            start = perf_counter()
            for _ in range(count):
                operation(structure)
            elapsed = (perf_counter() - start) / count
        finally:
            if collecting:
                gc.enable()
        if repeat:
            times.append(elapsed)
    return [float(value) for value in np.quantile(times, [.5, .25, .75])]


def _array_builder(array_class, n: int, spare: int):
    def build():
        array = array_class(n + spare)
        for value in range(n):
            array.append(value)
        return array

    return build


def _list_builder(list_class, n: int):
    def build():
        linked = list_class()
        for value in range(n):
            linked.append(value)
        return linked

    return build


ARRAY_OPERATIONS = {
    "вставка в начало": (lambda structure: structure.insert(0, -1), "insert"),
    "вставка в конец": (lambda structure: structure.append(-1), "append"),
    "удаление из начала": (lambda structure: structure.remove_at(0), "remove"),
    "доступ по индексу": (None, "get"),
}

LIST_OPERATIONS = {
    "вставка в начало": (lambda structure: structure.prepend(-1), "insert"),
    "вставка в конец": (lambda structure: structure.append(-1), "append"),
    "удаление из начала": (lambda structure: structure.remove_first(), "remove"),
    "доступ по индексу": (None, "get"),
}


def operations_table(array_class=None, list_classes: dict | None = None) -> pd.DataFrame:
    """Время четырёх операций; подготовка структуры не учитывается."""
    rows = []
    jobs = []
    if array_class is not None:
        available = implemented({"массив": array_class},
                                probe=lambda cls: cls(1).append(0))
        if not available:
            array_class = None
    for n in sizes():
        limit = max(4, n // 100)
        structures = []
        if array_class is not None:
            structures.append(("массив", ARRAY_OPERATIONS, _array_builder(array_class, n, limit + 8)))
        for name, list_class in (list_classes or {}).items():
            structures.append((name, LIST_OPERATIONS, _list_builder(list_class, n)))

        for structure_name, operations, build in structures:
            for operation_name, (operation, kind) in operations.items():
                if kind == "get":
                    call = lambda structure, index=n // 2: structure.get(index)  # noqa: E731
                else:
                    call = operation
                jobs.append((structure_name, operation_name, n, build, call,
                             4096 if kind == "get" else limit))
    for name, operation, n, build, call, limit in tqdm(
            jobs, desc="Время операций", unit="опыт"):
        median, q1, q3 = operation_time_stats(build, call, limit)
        rows.append({"Структура": name, "Операция": operation, "n": n,
                     "Время, с": median, "Время Q1, с": q1,
                     "Время Q3, с": q3})
    return pd.DataFrame(rows)


def _lookup_time_stats(table, keys) -> list[float]:
    """Медиана и квартили времени одного поиска по набору ключей."""
    keys = tuple(keys)
    if not keys:
        return [float("nan")] * 3

    def search_all(current):
        for key in keys:
            current.find(key)

    values = operation_time_stats(lambda: table, search_all, max_count=64)
    return [value / len(keys) for value in values]


def hash_grid_table(table_classes: dict, hash_functions: dict,
                    keys_name: str = "случайные строки") -> pd.DataFrame:
    """Коллизии хеша и время поиска в реализованных таблицах.

    Число слотов фиксировано, число ключей задаётся коэффициентом заполнения.
    Для каждой пары считаются коллизии и измеряется время успешного и
    неуспешного поиска.
    """
    make_keys = KEY_SETS[keys_name]
    capacity = hash_capacity()
    rows = []
    for table_name, table_class in table_classes.items():
        for hash_name, hash_function in hash_functions.items():
            for alpha in LOAD_FACTORS:
                count = int(capacity * alpha)
                keys = make_keys(count, seed=17)
                # Ключи, которых в таблице нет: тот же набор, другой seed.
                present = set(keys)
                absent = [key for key in make_keys(count, seed=999)
                          if key not in present][:200]

                table = table_class(capacity, hash_function)
                for key in keys:
                    table.insert(key, key)

                # Коллизия — попадание двух ключей в один исходный слот.
                # Метрика зависит только от хеш-функции и набора ключей, а не
                # от способа разрешения коллизий или скорости компьютера.
                home = {hash_function(key, capacity) for key in keys}
                collisions = count - len(home)

                sample = random.Random(101).sample(keys, min(500, count))
                found, found_q1, found_q3 = _lookup_time_stats(table, sample)
                missing, missing_q1, missing_q3 = _lookup_time_stats(table, absent)

                rows.append(
                    {
                        "Вариант": f"{table_name} · {hash_name}",
                        "Таблица": table_name,
                        "Хеш": hash_name,
                        "Данные": keys_name,
                        "Заполненность α": alpha,
                        "Элементов": len(table),
                        "Коллизий": collisions,
                        "Доля ключей с коллизией": collisions / max(1, count),
                        "Время успешного поиска, с": found,
                        "Время успешного поиска Q1, с": found_q1,
                        "Время успешного поиска Q3, с": found_q3,
                        "Время неуспешного поиска, с": missing,
                        "Время неуспешного поиска Q1, с": missing_q1,
                        "Время неуспешного поиска Q3, с": missing_q3,
                    }
                )
    return pd.DataFrame(rows)
