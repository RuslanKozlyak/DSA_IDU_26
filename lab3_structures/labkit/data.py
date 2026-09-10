"""Размеры структур и генерация ключей для работы 3."""

from __future__ import annotations

import random

from .core import pick

# Шаг — удвоение: по трём точкам наклон определяется двумя отрезками и любой
# выброс ломает картину, а отношение соседних значений при удвоении n прямо
# даёт порядок роста — 1 для O(1) и 2 для O(n).
FAST_SIZES = [1_000, 2_000, 4_000, 8_000, 16_000, 32_000]
FULL_SIZES = [1_000, 2_000, 4_000, 8_000, 16_000, 32_000, 64_000]

# Число слотов простое: у простого m нет общих делителей с шагом
# последовательности ключей, и регулярность ключей не переносится на номера
# слотов.
FAST_HASH_CAPACITY = 1_009
FULL_HASH_CAPACITY = 4_001

# Обе реализации проверяются на одних и тех же значениях заполненности, иначе
# их не с чем сравнивать. Единица недостижима для открытой адресации: там
# ячейка хранит не более одного элемента.
LOAD_FACTORS = [0.25, 0.50, 0.70, 0.90]

# Основание полиномиального хеша. Берётся не меньше размера алфавита: при
# меньшем основании соседние разряды перекрываются и позиционная запись
# теряет смысл.
POLY_BASE = 31

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
ANAGRAM_LETTERS = "abcdefgh"


def sizes() -> list[int]:
    return list(pick(FAST_SIZES, FULL_SIZES))


def hash_capacity() -> int:
    return pick(FAST_HASH_CAPACITY, FULL_HASH_CAPACITY)


def random_string_keys(count: int, seed: int = 42, length: int = 8) -> list[str]:
    """Различные случайные строки одинаковой длины.

    Обычные данные: ни порядок символов, ни их состав ничем не выделены.
    """
    rng = random.Random(seed + count)
    keys: set[str] = set()
    while len(keys) < count:
        keys.add("".join(rng.choice(ALPHABET) for _ in range(length)))
    return list(keys)


def anagram_keys(count: int, seed: int = 42,
                 letters: str = ANAGRAM_LETTERS) -> list[str]:
    """Различные перестановки одного и того же набора символов.

    Данные, неудобные для суммы кодов: сумма у всех перестановок одна, и такая
    хеш-функция сводит весь набор в один слот. Полиномиальный хеш учитывает
    позицию символа и должен распределить те же ключи существенно ровнее.
    """
    rng = random.Random(seed + count)
    base = list(letters)
    keys: set[str] = set()
    limit = 200 * max(count, 1)
    attempts = 0
    while len(keys) < count and attempts < limit:
        rng.shuffle(base)
        keys.add("".join(base))
        attempts += 1
    if len(keys) < count:
        raise ValueError(
            f"из {len(letters)} символов нельзя получить {count} перестановок")
    return list(keys)


# Наборы ключей, на которых сравниваются хеш-функции. Имя набора попадает в
# заголовок фигуры.
KEY_SETS = {
    "случайные строки": random_string_keys,
    "анаграммы": anagram_keys,
}

