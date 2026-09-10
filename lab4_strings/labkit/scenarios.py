"""One table per experiment: correctness and uninstrumented timing."""
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from .benchmark import time_samples, summarize
from .checks import expected_positions
from .core import pick
from .data import (text_sizes, pattern_sizes, fixed_text_size, random_text,
                   pattern_from_text, generate_log)

RANDOM = 'Случайный текст'
FOUND, MISSING = 'Образец есть', 'Образца нет'
BY_TEXT, BY_PATTERN = 'Растёт длина текста n', 'Растёт длина образца m'
SCALING_RANDOM = 'Случайный текст'
SCALING_FALLBACKS = 'Длинное несовпадение'
SCALING_MATCHES = 'Много вхождений'
FAST_SCALING_SIZES = (50, 100, 200, 400, 800)
FULL_SCALING_SIZES = (100, 200, 400, 800, 1_600)
SEEDS = [17,43,89]


def _measure(searches, jobs, description):
    rows=[]
    with tqdm(total=len(jobs)*len(searches),desc=description,unit='опыт') as progress:
        for case,x,cases in jobs:
            # Inputs and trusted answers are shared across all algorithms.
            prepared=[(text,pattern,expected_positions(text,pattern)) for text,pattern in cases]
            for name,func in searches.items():
                samples=[]
                for text,pattern,expected in prepared:
                    if func(text,pattern)!=expected:
                        raise AssertionError(f'{name}: неверный ответ, {case}, x={x}')
                    samples.extend(time_samples(lambda:func(text,pattern)))
                rows.append({'Алгоритм':name,'Сценарий':case,'x':x,
                             'n':len(prepared[0][0]),'m':len(prepared[0][1]),
                             'Входов':len(prepared),'Замеров на вход':7,
                             **summarize(samples)})
                progress.update()
    return pd.DataFrame(rows)


def size_experiment(searches, text_grid=None, pattern_grid=None, n=None):
    """Один рисунок на два размера: растёт длина текста, растёт длина образца.

    В левой колонке длина образца фиксирована, в правой — длина текста.
    Тексты и образцы общие для всех алгоритмов.
    """
    jobs = []
    for size in text_sizes() if text_grid is None else text_grid:
        cases = []
        for seed in SEEDS:
            text = random_text(size, seed=seed)
            cases.append((text, pattern_from_text(text, min(20, size // 2))))
        jobs.append((BY_TEXT, size, cases))
    fixed = fixed_text_size() if n is None else n
    texts = [random_text(fixed, seed=seed) for seed in SEEDS]
    for m in pattern_sizes() if pattern_grid is None else pattern_grid:
        jobs.append((BY_PATTERN, m,
                     [(text, pattern_from_text(text, m)) for text in texts]))
    return _measure(searches, jobs, 'Размер входа')






def log_experiment(searches, text=None):
    text=generate_log() if text is None else text
    signatures=['ERROR','WARNING','database timeout','cache hit']
    jobs=[(signature,signature,[(text,signature)]) for signature in signatures]
    return _measure(searches,jobs,'Сигнатуры журнала'),text


def scaling_experiment(searches, size_grid=None, pattern_ratio=10):
    """Время алгоритмов при одновременном росте n и m на трёх типах входа."""
    if not searches:
        return pd.DataFrame(columns=['Алгоритм', 'Сценарий', 'n', 'm', 'n + m',
                                     'Время, с', 'Время Q1, с', 'Время Q3, с',
                                     'Время на символ, с'])
    if not isinstance(pattern_ratio, int) or pattern_ratio < 2:
        raise ValueError('pattern_ratio должно быть целым числом не меньше 2')
    default_sizes = pick(FAST_SCALING_SIZES, FULL_SCALING_SIZES)
    sizes = list(default_sizes if size_grid is None else size_grid)
    if not sizes or any(not isinstance(n, int) or n < pattern_ratio for n in sizes):
        raise ValueError('Размеры текста должны быть целыми и не меньше pattern_ratio')

    rows = []
    for n in sorted(set(sizes)):
        m = n // pattern_ratio
        random = random_text(n, seed=17)
        mismatch_at = 3 * m // 4
        cases = [
            (SCALING_RANDOM, random, pattern_from_text(random, m)),
            (SCALING_FALLBACKS, 'a' * n,
             'a' * mismatch_at + 'b' + 'a' * (m - mismatch_at - 1)),
            (SCALING_MATCHES, 'a' * n, 'a' * m),
        ]
        for name, search in searches.items():
            for case, text, pattern in cases:
                expected = expected_positions(text, pattern)
                if search(text, pattern) != expected:
                    raise AssertionError(f'{name}: неверный ответ, {case}, n={n}, m={m}')
                total_size = n + m
                stats = summarize(time_samples(lambda: search(text, pattern)))
                rows.append({'Алгоритм': name, 'Сценарий': case, 'n': n, 'm': m,
                             'n + m': total_size, 'Входов': 1, 'Замеров на вход': 7,
                             **stats, 'Время на символ, с': stats['Время, с'] / total_size,
                             'Время на символ Q1, с': stats['Время Q1, с'] / total_size,
                             'Время на символ Q3, с': stats['Время Q3, с'] / total_size})
    return pd.DataFrame(rows)
