"""Проверка требований к устройству решения по байт-коду.

Разбор исходного текста здесь не годится: в ноутбуке исходники ячеек не всегда
доступны, а комментарии и строки дают ложные срабатывания. Байт-код доступен
всегда и не зависит от оформления.
"""

from __future__ import annotations

import dis
from types import CodeType


def _all_codes(func) -> list[CodeType]:
    """Код функции и всех вложенных в неё функций и генераторов."""
    code = func.__code__
    found = [code]
    stack = [code]
    while stack:
        current = stack.pop()
        for constant in current.co_consts:
            if isinstance(constant, CodeType):
                found.append(constant)
                stack.append(constant)
    return found


def uses_loops(func) -> bool:
    """Есть ли в функции цикл: `for`, `while` или генераторное выражение."""
    for code in _all_codes(func):
        for instruction in dis.get_instructions(code):
            if instruction.opname == "FOR_ITER":
                return True
            if instruction.opcode in dis.hasjabs or instruction.opcode in dis.hasjrel:
                target = instruction.argval
                if isinstance(target, int) and target < instruction.offset:
                    return True
    return False


def uses_slices(func) -> bool:
    """Используются ли срезы вида `text[a:b]`."""
    for code in _all_codes(func):
        for instruction in dis.get_instructions(code):
            if instruction.opname in ("BUILD_SLICE", "BINARY_SLICE", "STORE_SLICE"):
                return True
    return False


def is_recursive(func) -> bool:
    """Вызывает ли функция саму себя по имени."""
    name = func.__name__
    for code in _all_codes(func):
        if name in code.co_names or name in code.co_freevars:
            return True
    return False


def calls_global(func, name: str) -> bool:
    """Обращается ли функция к глобальному имени: `sorted(...)`, `re`, `bisect`.

    Локальные функции и переменные с тем же именем сюда не попадают: у них
    другие инструкции загрузки.
    """
    for code in _all_codes(func):
        for instruction in dis.get_instructions(code):
            if instruction.opname in ("LOAD_GLOBAL", "LOAD_NAME", "IMPORT_NAME"):
                if instruction.argval == name:
                    return True
    return False


def calls_method(func, name: str) -> bool:
    """Вызывает ли функция метод с указанным именем: `arr.sort()`, `text.find()`."""
    for code in _all_codes(func):
        for instruction in dis.get_instructions(code):
            if instruction.opname in ("LOAD_METHOD", "LOAD_ATTR") and instruction.argval == name:
                return True
    return False
