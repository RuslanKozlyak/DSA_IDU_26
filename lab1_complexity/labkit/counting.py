"""Подсчёт обращений к элементам массива.

Счётчик вынесен из алгоритма: студент пишет обычный поиск по `arr[i]`,
а инфраструктура подставляет вместо списка объект, который считает обращения.
"""

from __future__ import annotations


class CountingArray:
    """Обёртка над списком, считающая операции чтения `arr[i]`."""

    def __init__(self, data) -> None:
        self._data = list(data)
        self.accesses = 0
        self.indices = []

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index):
        if isinstance(index, slice):
            positions = list(range(*index.indices(len(self._data))))
            self.accesses += len(positions)
            self.indices.extend(positions)
            return self._data[index]
        value = self._data[index]
        self.accesses += 1
        self.indices.append(index)
        return value

    def __iter__(self):
        for index in range(len(self._data)):
            yield self[index]

    def index(self, value, start=0, stop=None):
        """Аналог list.index с честным подсчётом просмотренных элементов."""
        size = len(self._data)
        start, stop, _ = slice(start, size if stop is None else stop).indices(size)
        for index in range(start, stop):
            if self[index] == value:
                return index
        raise ValueError(f"{value!r} is not in list")

    def count(self, value):
        """Аналог list.count с честным подсчётом просмотренных элементов."""
        return sum(1 for item in self if item == value)

    def __repr__(self) -> str:
        return f"CountingArray(len={len(self._data)}, accesses={self.accesses})"


def count_accesses(search_func, data, target):
    """Выполнить поиск и вернуть пару «результат, число обращений»."""
    arr = CountingArray(data)
    result = search_func(arr, target)
    return result, arr.accesses


def trace_accesses(search_func, data, target):
    """Результат поиска и последовательность прочитанных индексов."""
    arr = CountingArray(data)
    result = search_func(arr, target)
    return result, list(arr.indices)
