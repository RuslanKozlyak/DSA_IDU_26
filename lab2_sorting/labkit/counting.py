"""Подсчёт сравнений, шагов циклов и обращений к элементам массива.

Счётчики вынесены из алгоритма: студент пишет обычную сортировку. Для
сравнительных алгоритмов инфраструктура подставляет объекты, считающие
сравнения. Для распределительных алгоритмов трассируются шаги циклов в самой
реализации и вызываемых ею пользовательских помощниках.
"""

from __future__ import annotations

import dis
import sys
from types import CodeType, FunctionType


class AccessCounter:
    """Чтения и записи элементов, а не байты занятой памяти."""

    def __init__(self):
        self.reads = 0
        self.writes = 0


class CountingList(list):
    """Входной список и его срезы/copy() с общим счётчиком.

    Индексное чтение/запись стоят одно обращение, срез — по одному на
    элемент. Итерация (включая max и list) учитывает каждое чтение.
    len, работа с локальными переменными и внутренние сдвиги Python не
    учитываются. Новые обычные списки, созданные алгоритмом, не отслеживаются.
    """

    def __init__(self, data=(), counter=None):
        super().__init__(data)
        self.counter = counter if counter is not None else AccessCounter()

    def __getitem__(self, index):
        result = super().__getitem__(index)
        if isinstance(index, slice):
            self.counter.reads += len(result)
            return CountingList(result, self.counter)
        self.counter.reads += 1
        return result

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            values = list(value)
            super().__setitem__(index, values)
            self.counter.writes += len(values)
        else:
            super().__setitem__(index, value)
            self.counter.writes += 1

    def __iter__(self):
        for value in super().__iter__():
            self.counter.reads += 1
            yield value

    def __reversed__(self):
        for value in super().__reversed__():
            self.counter.reads += 1
            yield value

    def copy(self):
        return self[:]

    def append(self, value):
        super().append(value)
        self.counter.writes += 1

    def extend(self, values):
        for value in list(values):
            self.append(value)

    def __iadd__(self, values):
        self.extend(values)
        return self

    def insert(self, index, value):
        super().insert(index, value)
        self.counter.writes += 1

    def pop(self, index=-1):
        value = super().pop(index)
        self.counter.reads += 1
        return value

    def reverse(self):
        super().reverse()
        touched = 2 * (len(self) // 2)
        self.counter.reads += touched
        self.counter.writes += touched


def count_accesses(sort_func, data) -> dict[str, int]:
    """Отдельный прогон: обращения к входу и его отслеживаемым копиям.

    Подготовка входа и проверка результата в счёт не входят. Вспомогательные
    массивы счётчиков/блоков не охвачены: это не полное число операций сортировки.
    """
    arr = CountingList(data)
    sort_func(arr)
    return {
        "Чтений": arr.counter.reads,
        "Записей": arr.counter.writes,
        "Обращений": arr.counter.reads + arr.counter.writes,
    }


class Counter:
    """Накопитель числа сравнений одного прогона."""

    def __init__(self) -> None:
        self.comparisons = 0


ACTIVE = Counter()


class CountedInt(int):
    """Целое, считающее сравнения. Во всём остальном — обычное `int`."""

    __slots__ = ()

    def __lt__(self, other):
        ACTIVE.comparisons += 1
        return int(self) < int(other)

    def __le__(self, other):
        ACTIVE.comparisons += 1
        return int(self) <= int(other)

    def __gt__(self, other):
        ACTIVE.comparisons += 1
        return int(self) > int(other)

    def __ge__(self, other):
        ACTIVE.comparisons += 1
        return int(self) >= int(other)

    def __eq__(self, other):
        ACTIVE.comparisons += 1
        return int(self) == int(other)

    def __ne__(self, other):
        ACTIVE.comparisons += 1
        return int(self) != int(other)

    def __hash__(self) -> int:
        return int.__hash__(self)


class CountedFloat(float):
    """Вещественное, считающее сравнения. Нужно блочной сортировке."""

    __slots__ = ()

    def __lt__(self, other):
        ACTIVE.comparisons += 1
        return float(self) < float(other)

    def __le__(self, other):
        ACTIVE.comparisons += 1
        return float(self) <= float(other)

    def __gt__(self, other):
        ACTIVE.comparisons += 1
        return float(self) > float(other)

    def __ge__(self, other):
        ACTIVE.comparisons += 1
        return float(self) >= float(other)

    def __eq__(self, other):
        ACTIVE.comparisons += 1
        return float(self) == float(other)

    def __ne__(self, other):
        ACTIVE.comparisons += 1
        return float(self) != float(other)

    def __hash__(self) -> int:
        return float.__hash__(self)


def wrap(data):
    """Обернуть значения в считающие объекты, не меняя порядка."""
    kind = CountedFloat if any(isinstance(x, float) for x in data) else CountedInt
    return [kind(x) for x in data]


def count_comparisons(sort_func, data) -> int:
    """Выполнить сортировку и вернуть число сравнений между элементами.

    Арифметика над значениями возвращает обычные числа, поэтому вычисленные
    величины (разряд, номер корзины) в счёт не попадают — считаются только
    сравнения самих элементов друг с другом.
    """
    global ACTIVE
    ACTIVE = Counter()
    sort_func(wrap(data))
    return ACTIVE.comparisons


def _nested_codes(code):
    """Код функции и всех вложенных функций/генераторов."""
    found = {code}
    stack = [code]
    while stack:
        current = stack.pop()
        for constant in current.co_consts:
            if isinstance(constant, CodeType) and constant not in found:
                found.add(constant)
                stack.append(constant)
    return found


def _algorithm_codes(sort_func):
    """Код сортировки и вызываемых ею пользовательских помощников."""
    found = set()
    pending = [sort_func]
    visited = set()
    while pending:
        func = pending.pop()
        if func in visited:
            continue
        visited.add(func)
        codes = _nested_codes(func.__code__)
        found.update(codes)
        for code in codes:
            for name in code.co_names:
                candidate = func.__globals__.get(name)
                if isinstance(candidate, FunctionType) and candidate not in visited:
                    pending.append(candidate)
    return found


def count_loop_steps(sort_func, data) -> int:
    """Число выполненных шагов циклов в коде сортировки и её помощников.

    Считаются посещения строк управления циклами Python. Завершающая проверка
    тоже может входить в счёт. Встроенные операции на одной строке могут иметь
    разную стоимость, поэтому это индикатор объёма циклической работы, а не
    универсальное «число всех операций».
    """
    codes = _algorithm_codes(sort_func)
    loop_lines = {}
    for code in codes:
        targets = {
            instruction.argval
            for instruction in dis.get_instructions(code)
            if instruction.opcode in (*dis.hasjabs, *dis.hasjrel)
            and isinstance(instruction.argval, int)
            and instruction.argval < instruction.offset
        }
        lines = {
            line
            for start, end, line in code.co_lines()
            for target in targets
            if start <= target < end and line is not None
        }
        if lines:
            loop_lines[code] = lines

    total = 0
    previous_trace = sys.gettrace()

    def trace(frame, event, arg):
        nonlocal total
        if event == "call":
            if frame.f_code in loop_lines:
                return trace
            return None
        if event == "line" and frame.f_lineno in loop_lines.get(frame.f_code, ()):
            total += 1
        return trace

    sys.settrace(trace)
    try:
        result = sort_func(list(data))
    finally:
        sys.settrace(previous_trace)
    if result is None or list(result) != sorted(data):
        raise ValueError("Сортировка вернула неверный результат при подсчёте циклов")
    return total


def count_metrics(sort_func, data) -> dict[str, int]:
    """Сравнения и обращения за один инструментированный запуск.

    Подготовка и проверка результата не входят в счёт. Счётчики покрывают
    операции обёрток, а не все действия Python; арифметика теряет обёртку.
    """
    global ACTIVE
    ACTIVE = Counter()
    arr = CountingList(wrap(data))
    result = sort_func(arr)
    metrics = {"Сравнений": ACTIVE.comparisons,
               "Чтений": arr.counter.reads, "Записей": arr.counter.writes,
               "Обращений": arr.counter.reads + arr.counter.writes}
    if result is None or list(result) != sorted(data):
        raise ValueError("Сортировка вернула неверный результат на данных эксперимента")
    return metrics
