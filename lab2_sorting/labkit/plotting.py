"""Графики работы 2.

Панели строятся по общей сетке. В опыте с разными входными данными две
одинаковые сетки отдельно показывают время и число обращений к элементам.
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import (FixedFormatter, FixedLocator, FuncFormatter, MaxNLocator,
                               LogLocator, ScalarFormatter)

MARKERS = ("o", "s", "^", "D", "v", "P", "X")

# Квадратичный алгоритм даёт на элемент в сотни раз больше остальных и на общей
# шкале прижимает все прочие кривые к нулю. На панелях «на элемент» он выносится
# отдельно; на логарифмических панелях он остаётся вместе со всеми.
QUADRATIC = ("пузырьк",)


def _is_quadratic(name: str) -> bool:
    return any(key in name.lower() for key in QUADRATIC)


def _tick_label(n: float) -> str:
    n = int(n)
    return f"{n // 1000}k" if n >= 1000 and n % 1000 == 0 else str(n)


def _number(value: float) -> str:
    """Подпись значения без показателя степени: `10 000`, а не `1e+04`."""
    if abs(value) >= 1000:
        return f"{value:,.0f}".replace(",", "\u202f")
    return f"{value:.3g}"


def _readable_ticks(axis) -> None:
    """Подписи логарифмической оси, когда порядков мало.

    На диапазоне уже двух порядков между `10^k` подписей не остаётся вовсе:
    ось получает одно деление на всю панель. Тогда добавляются промежуточные
    деления на 2 и 5, а сами числа печатаются как числа, а не как `2x10^0`.
    """
    low, high = axis.get_ylim()
    if low <= 0 or high <= low or high / low > 200:
        return
    narrow = high / low <= 12
    if not narrow:
        axis.yaxis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))
        axis.yaxis.set_minor_locator(
            LogLocator(base=10, subs=tuple(range(2, 10)), numticks=100))
    for setter in ((axis.yaxis.set_major_formatter,) if not narrow else
                   (axis.yaxis.set_major_formatter, axis.yaxis.set_minor_formatter)):
        scalar = ScalarFormatter()
        scalar.set_scientific(False)
        setter(scalar)


def _headroom(axis) -> None:
    """Запас сверху, чтобы подписи концов кривых не упирались в рамку."""
    low, high = axis.get_ylim()
    if axis.get_yscale() == "log":
        axis.set_ylim(low, high * 1.6)
    else:
        axis.set_ylim(low, high + (high - low) * 0.12)


def _annotate_ends(axis, entries) -> None:
    """Подписи концов кривых; близкие по высоте разводятся по вертикали.

    Две серии могут прийти почти в одну точку — например, у сортировок
    подсчётом и поразрядной работа на элемент почти одинакова. Тогда подписи
    легли бы одна на другую и обе стали бы нечитаемы. Близость считается по
    доле высоты панели, а не по разнице значений: на логарифмической шкале
    это разные вещи. Вызывать после того, как границы осей уже выставлены.
    """
    low, high = axis.get_ylim()
    logarithmic = axis.get_yscale() == "log"

    def height(value: float) -> float:
        if logarithmic:
            if value <= 0 or low <= 0 or high <= low:
                return 0.0
            return math.log10(value / low) / math.log10(high / low)
        return (value - low) / (high - low) if high > low else 0.0

    previous = None
    shift = 0.0
    for x, y, text in sorted(entries, key=lambda item: item[1]):
        if previous is not None and height(y) - height(previous) < 0.045:
            shift += 11
        else:
            shift = 0.0
        axis.annotate(text, (x, y), textcoords="offset points",
                      xytext=(5, shift), fontsize=8, va="center")
        previous = y


def _size_axis(axis, points, linear=False) -> None:
    if linear:
        axis.set_xscale("linear")
        axis.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        axis.xaxis.set_major_formatter(FuncFormatter(lambda x, _: _tick_label(x)))
        axis.set_xlim(0, max(points, default=1) * 1.08)
        return
    axis.set_xscale("log")
    axis.xaxis.set_major_locator(FixedLocator(points))
    axis.xaxis.set_major_formatter(FixedFormatter([_tick_label(n) for n in points]))
    axis.xaxis.set_minor_locator(FixedLocator([]))
    axis.margins(x=0.18)


def _panel(axis, table, value, series="Алгоритм", names=None, x="n",
           scale=1.0, per_element=False, logy=False, reference_log=False,
           annotate=None, headroom: bool = True, linear_x=False,
           reference_linear=False) -> None:
    """Одна панель: кривые по сериям на общей сетке.

    `per_element=True` делит величину на `n`. Это существенно: на
    логарифмическом графике `n` и `n log n` дают наклоны 1,0 и примерно 1,1,
    и кривые сливаются в пучок почти параллельных прямых. После деления на `n`
    линейный алгоритм становится горизонтальной линией, `n log n` — прямой с
    постоянным подъёмом, а квадратичный загибается вверх.
    """
    if names is None:
        names = list(table[series].unique())
    if annotate is None:
        annotate = per_element
    points = sorted({int(v) for name in names for v in table[table[series] == name][x]})
    ends = []
    for index, name in enumerate(names):
        part = table[table[series] == name].sort_values(x)
        values = part[value] / part["n"] * scale if per_element else part[value] * scale
        axis.plot(part[x], values, marker=MARKERS[index % len(MARKERS)],
                  markersize=4.5, label=str(name))
        if len(values):
            ends.append((list(part[x])[-1], list(values)[-1],
                         _number(list(values)[-1])))
    if reference_log and points:
        low, high = min(points), max(points)
        # Теоретический ориентир без подбора коэффициентов по данным.
        grid = [low + (high - low) * i / 400 for i in range(401)]
        values = [math.log2(n) * (1 if per_element else n) for n in grid]
        label = "log₂ n" if per_element else "n · log₂ n"
        axis.plot(grid, values, linestyle="--",
                  linewidth=1.7, color="0.25", label=label, zorder=3)
    if reference_linear and points:
        ends_x = [min(points), max(points)]
        axis.plot(ends_x, [1, 1] if per_element else ends_x, linestyle=":",
                  linewidth=2, color="black", label="1" if per_element else "n", zorder=3)
    _size_axis(axis, points, linear=linear_x)
    if logy:
        axis.set_yscale("log")
        _readable_ticks(axis)
    else:
        axis.set_ylim(bottom=0)
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(fontsize=8, loc="upper left")
    if headroom:
        _headroom(axis)
        if annotate:
            _annotate_ends(axis, ends)
    return ends


def plot_growth(table: pd.DataFrame) -> None:
    """Рост времени с размером массива: время целиком и время на элемент.

    Левая панель — то, что показывает секундомер: кривые идут почти
    параллельно, потому что различие между `n` и `n log n` на логарифмической
    шкале составляет около десятой доли наклона. Правая — то же время,
    делённое на `n`: линейные алгоритмы выходят на горизонталь, `n log n`
    растут.
    """
    names = list(table["Алгоритм"].unique())
    light = [name for name in names if not _is_quadratic(name)]

    figure, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    _panel(axes[0], table, "Время, с", logy=True)
    axes[0].set(title="Время работы", xlabel="Размер массива n", ylabel="Время, с")

    _panel(axes[1], table, "Время, с", names=light, scale=1e6, per_element=True)
    axes[1].set(title="Время на один элемент", xlabel="Размер массива n",
                ylabel="Время / n, мкс")

    figure.suptitle("Рост с размером массива   ·   справа квадратичная не показана")
    figure.tight_layout()
    plt.show()


def plot_comparisons(table: pd.DataFrame) -> None:
    """Полное число сравнений по размеру массива: обе оси обычные."""
    names = list(table["Алгоритм"].unique())
    heavy = [name for name in names if _is_quadratic(name)]
    light = [name for name in names if name not in heavy]

    groups = [light, heavy] if light and heavy else [names]
    figure, axes = plt.subplots(1, len(groups), figsize=(8 * len(groups), 5), squeeze=False)
    for axis, group in zip(axes[0], groups):
        _panel(axis, table, "Сравнений", names=group, linear_x=True,
               reference_log=True, reference_linear=True, annotate=False)
        axis.set(title=("Пузырьковая: отдельная шкала" if len(groups) > 1 and group == heavy
                        else "Число сравнений"),
                 xlabel="Размер массива n", ylabel="Число сравнений")
        axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: _number(value)))
    figure.suptitle("Число сравнений и размер массива · ориентиры n и n · log₂ n без подгонки")
    figure.tight_layout()
    plt.show()


def _grid(count: int):
    """Сетка панелей: не длиннее двух в высоту, не шире двух в ширину."""
    if count <= 1:
        return 1, 1
    if count == 2:
        return 1, 2
    if count <= 4:
        return 2, 2
    return 2, (count + 1) // 2


def _facets(table, facet, value, series, title, xlabel, ylabel,
            logy=True, per_element=False, scale=1.0) -> None:
    """Одна фигура, по панели на каждое значение `facet`, шкалы общие."""
    keys = list(table[facet].unique())
    rows, columns = _grid(len(keys))
    figure, axes = plt.subplots(rows, columns, figsize=(6.2 * columns, 4.4 * rows),
                                squeeze=False, sharey=True)
    flat = [axis for row in axes for axis in row]
    for axis, key in zip(flat, keys):
        _panel(axis, table[table[facet] == key], value, series=series,
               logy=logy, per_element=per_element, scale=scale, annotate=False,
               headroom=False)
        axis.set(title=str(key), xlabel=xlabel)
    # Шкала общая, поэтому запас берётся один раз, когда все панели уже
    # нарисованы: иначе границы считались бы по данным первой из них.
    _headroom(flat[0])
    for axis in flat[len(keys):]:
        axis.set_visible(False)
    for row in axes:
        row[0].set_ylabel(ylabel)
    figure.suptitle(title)
    figure.tight_layout()
    plt.show()


def plot_datasets(table: pd.DataFrame) -> None:
    """Две одинаковые сетки: время и логические обращения на шести наборах."""
    _facets(table, "Тип данных", "Время, с", "Алгоритм",
            "Время работы на разных входных данных",
            "Размер массива n", "Время, с")
    _facets(table, "Тип данных", "Обращений", "Алгоритм",
            "Обращения к входному списку и его срезам на разных данных",
            "Размер массива n", "Обращений (чтения + записи)")


def plot_radix_digits(table: pd.DataFrame) -> None:
    """Поразрядная сортировка: время в зависимости от числа разрядов."""
    figure, axis = plt.subplots(figsize=(8, 4.6))
    axis.plot(table["Разрядов"], table["Время, с"], marker="o")
    axis.set(xlabel="Число разрядов d", ylabel="Время, с")
    axis.set_ylim(bottom=0)
    axis.set_xticks(list(table["Разрядов"]))
    axis.grid(True, alpha=0.25)
    figure.suptitle("Поразрядная сортировка: влияние числа разрядов")
    figure.tight_layout()
    plt.show()


def plot_bucket_distributions(table: pd.DataFrame) -> None:
    """Блочная сортировка: равномерное и сконцентрированное распределение."""
    figure, axis = plt.subplots(figsize=(9, 4.8))
    _panel(axis, table, "Время, с", series="Распределение", logy=True)
    axis.set(title="Блочная сортировка: распределение значений",
             xlabel="Размер массива n", ylabel="Время, с")
    figure.tight_layout()
    plt.show()
