"""Инфраструктура лабораторной работы 4."""

from .checks import (check_prefix_function, check_same_results, check_search,
                     check_signature_analysis, expected_positions)
from .core import (
    CONFIG,
    Checker,
    format_seconds,
    measure_time,
    use_full_sizes,
)
from .scenarios import log_experiment, scaling_experiment, size_experiment
from .scenario_plots import plot_log_experiment, plot_scaling, plot_search_experiment
from .data import SIGNATURES, SMALL_LOG, generate_log, pattern_sizes, random_text, text_sizes
from .experiments import (
    big_log_table,
    found_missing_table,
    hard_case_table,
    implemented_searches,
    pattern_length_table,
    signature_table,
    text_length_table,
)
from .plotting import (
    plot_big_log,
    plot_found_missing,
    plot_pattern_length,
    plot_text_length,
)

__all__ = [
    "CONFIG",
    "Checker",
    "SIGNATURES",
    "SMALL_LOG",
    "big_log_table",
    "check_prefix_function",
    "check_same_results",
    "check_search",
    "expected_positions",
    "format_seconds",
    "found_missing_table",
    "generate_log",
    "hard_case_table",
    "implemented_searches",
    "measure_time",
    "pattern_length_table",
    "pattern_sizes",
    "plot_big_log",
    "plot_found_missing",
    "plot_pattern_length",
    "plot_text_length",
    "random_text",
    "signature_table",
    "text_length_table",
    "text_sizes",
    "use_full_sizes",
    "size_experiment",
    "scaling_experiment",
    "log_experiment",
    "plot_search_experiment",
    "plot_scaling",
    "plot_log_experiment",
]
