"""Paired metrics on identical inputs for search-position experiments."""
import pandas as pd
from tqdm.auto import tqdm
from .benchmark import time_samples, summarize
from .core import pick
from .counting import count_accesses

CASES = ["В начале", "В середине", "В конце", "Не найден"]
FAST_GRID = [10, 32, 64, 100, 128, 256, 512, 1000, 2000, 4000, 6000, 8000, 10000]
FULL_GRID = FAST_GRID + [20000, 40000, 60000, 80000, 100000]


def search_cases_table(searches, grid=None):
    points = list(pick(FAST_GRID, FULL_GRID) if grid is None else grid)
    rows = []
    jobs = [(n, case, name, func) for n in points for case in CASES
            for name, func in searches.items()]
    for n, case, name, func in tqdm(jobs, desc="Поиск: время и обращения", unit="опыт"):
        if n < 1:
            raise ValueError("Эксперимент требует n >= 1")
        array = list(range(n))
        target = {CASES[0]:0, CASES[1]:(n-1)//2, CASES[2]:n-1, CASES[3]:n}[case]
        expected = target if target < n else -1
        result, count = count_accesses(func, array, target)
        if result != expected or func(array, target) != expected:
            raise AssertionError(f"{name}: неверный ответ, n={n}, {case}")
        samples = time_samples(lambda: func(array, target))
        rows.append({"Алгоритм":name, "Сценарий":case, "n":n,
                     "Обращений":count, **summarize(samples)})
    return pd.DataFrame(rows)
