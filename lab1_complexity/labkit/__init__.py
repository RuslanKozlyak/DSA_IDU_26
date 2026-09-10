"""Инфраструктура лабораторной работы 1.

Студент импортирует из этого пакета готовые тесты, эксперименты и графики.
"""

from .checks import check_palindrome, check_search
from .core import (
    CONFIG,
    Checker,
    format_seconds,
    measure_time,
    use_full_sizes,
)
from .counting import CountingArray, count_accesses
from .data import missing_target, sizes, sorted_array
from .experiments import accesses_table, time_table
from .plotting import plot_accesses, plot_times
from .scenarios import search_cases_table
from .scenario_plots import plot_search_overview, plot_search_positions

__all__ = [
    "CONFIG",
    "Checker",
    "CountingArray",
    "accesses_table",
    "check_palindrome",
    "check_search",
    "count_accesses",
    "format_seconds",
    "measure_time",
    "missing_target",
    "plot_accesses",
    "plot_times",
    "sizes",
    "sorted_array",
    "time_table",
    "use_full_sizes",
    "search_cases_table",
    "plot_search_overview",
    "plot_search_positions",
]
