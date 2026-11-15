import sys
from pathlib import Path

for candidate in [Path.cwd(), *Path.cwd().parents]:
    if (candidate / "labkit").is_dir():
        sys.path.insert(0, str(candidate))
        break

import labkit as lk

print("Режим:", lk.CONFIG.name, "| размеры массивов:", lk.sizes())


def linear_search(arr, target):
    """Индекс любого вхождения target в arr или -1, если его нет."""
    # TODO: реализовать линейный поиск
    length = len(arr)
    for pos in range(length):
        if arr[pos] == target:
            return pos
    else:
        return -1

    raise NotImplementedError("linear_search")

lk.check_search(linear_search, "Линейный поиск")


def binary_search(arr, target):
    """Индекс любого вхождения target в отсортированном arr или -1."""
    if arr:
        reference = [i for i in range(len(arr))]
        cur = "a"
        ind_cur = -1
        while cur != target:
            ind_cur = (len(reference) - 1)//2
            cur = arr[reference[ind_cur]]
            if cur > target:
                reference = reference[:ind_cur]
            if cur < target:
                reference = reference[ind_cur + 1:]
            if cur == target:
                return reference[ind_cur]
            if not reference:
                return -1
    else:
        return -1
        # TODO: реализовать двоичный поиск
    
        
    raise NotImplementedError("binary_search")


lk.check_search(binary_search, "Двоичный поиск", expect_logarithmic=True)


def is_palindrome(text, left=0, right=None):
    """True, если text читается одинаково в обе стороны."""
    # TODO: реализовать рекурсивно, без циклов и срезов
    if left < len(text):
        if left > len(text)//2:
            return True
        if text[left] == text[-left - 1]:
            return is_palindrome(text, left=(left + 1))
        else:
            return False
    else:
        return True
    raise NotImplementedError("is_palindrome")

lk.check_palindrome(is_palindrome)

SEARCHES = {"Линейный поиск": linear_search, "Двоичный поиск": binary_search}
search_cases = lk.search_cases_table(SEARCHES)
lk.plot_search_overview(search_cases)
lk.plot_search_positions(search_cases)


