"""Графики работы 4.

Каждый эксперимент даёт одну фигуру: панели внутри неё строятся по общей
сетке и различаются ровно одним параметром, поэтому сравнение делает глаз,
а не подпись под картинкой.
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import (FixedFormatter, FixedLocator,
                               LogLocator, ScalarFormatter)

MARKERS = ("o", "s", "^", "D", "v")


def _number(value: float) -> str:
    """Подпись значения без показателя степени: `10 000`, а не `1e+04`."""
    if abs(value) >= 1000:
        return f"{value:,.0f}".replace(",", "\u202f")
    return f"{value:.3g}"


def _tick_label(n: float) -> str:
    n = int(n)
    return f"{n // 1000}k" if n >= 1000 and n % 1000 == 0 else str(n)


def _size_axis(axis, points) -> None:
    """Ось размеров: подписи стоят ровно в тех точках, где ставился опыт."""
    axis.set_xscale("log")
    axis.xaxis.set_major_locator(FixedLocator(points))
    axis.xaxis.set_major_formatter(FixedFormatter([_tick_label(n) for n in points]))
    axis.xaxis.set_minor_locator(FixedLocator([]))
    axis.margins(x=0.18)


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


def _panel(axis, table, value, x="n", series="Алгоритм", scale=1.0,
           per_symbol=False, logy=True, annotate=True,
           headroom: bool = True) -> None:
    """Одна панель: кривые по алгоритмам на общей сетке.

    `per_symbol=True` делит величину на длину текста. Это существенно: на
    обычном тексте все три алгоритма линейны по `n` и дают три параллельные
    прямые. После деления на `n` остаётся работа, приходящаяся на один символ,
    и вот она у алгоритмов разная.
    """
    points = sorted({int(v) for v in table[x]})
    ends = []
    for index, name in enumerate(table[series].unique()):
        part = table[table[series] == name].sort_values(x)
        values = part[value] / part["n"] * scale if per_symbol else part[value] * scale
        axis.plot(part[x], values, marker=MARKERS[index % len(MARKERS)],
                  markersize=4.5, label=str(name))
        if len(values):
            ends.append((list(part[x])[-1], list(values)[-1],
                         _number(list(values)[-1])))
    _size_axis(axis, points)
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


def _ratio_panel(axis, table, value, x="n", series="Алгоритм") -> None:
    """Тест удвоения: отношение соседних значений при удвоении параметра.

    Отношение равно `2` у линейной по параметру величины, `4` у квадратичной
    и `1`, если величина от параметра не зависит вовсе.
    """
    labels = []
    for index, name in enumerate(table[series].unique()):
        part = table[table[series] == name].sort_values(x)
        points = [int(v) for v in part[x]]
        values = [float(v) for v in part[value]]
        labels, heights = [], []
        for step in range(1, len(points)):
            if points[step] != 2 * points[step - 1] or not values[step - 1]:
                continue
            labels.append(f"{_tick_label(points[step - 1])}\u2192"
                          f"{_tick_label(points[step])}")
            heights.append(values[step] / values[step - 1])
        axis.plot(range(len(heights)), heights,
                  marker=MARKERS[index % len(MARKERS)], markersize=4.5,
                  label=str(name))
    for level, note in ((1.0, "не зависит"), (2.0, "линейно"), (4.0, "квадратично")):
        axis.axhline(level, linestyle="--", linewidth=1.2, color="0.45", zorder=0)
        axis.text(0.995, level, note, transform=axis.get_yaxis_transform(),
                  ha="right", va="bottom", fontsize=8.5, color="0.35")
    axis.set_xticks(range(len(labels)))
    axis.set_xticklabels(labels, fontsize=8, rotation=20)
    axis.set_ylim(0, 4.6)
    axis.grid(True, axis="y", alpha=0.25)
    axis.legend(fontsize=8, loc="upper left")


def plot_text_length(table: pd.DataFrame) -> None:
    """Длина текста растёт: время целиком и время, приходящееся на символ.

    Слева три почти параллельные прямые — правильный результат: все три
    алгоритма линейны по `n`. Справа то же время, поделённое на `n`: линии
    выходят на горизонтали, и видно, чем алгоритмы отличаются на самом деле —
    постоянным множителем при `n`.
    """
    figure, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    _panel(axes[0], table, "Время, с", scale=1e6)
    axes[0].set(title="Время поиска", xlabel="Длина текста n", ylabel="Время, мкс")
    _panel(axes[1], table, "Время, с", scale=1e9, per_symbol=True, logy=False)
    axes[1].set(title="Время на один символ текста", xlabel="Длина текста n",
                ylabel="Время / n, нс")
    figure.suptitle("Влияние длины текста   \u00b7   справа то же время, "
                    "поделённое на n")
    figure.tight_layout()
    plt.show()


def plot_pattern_length(table: pd.DataFrame) -> None:
    """Длина образца растёт, длина текста постоянна."""
    figure, axis = plt.subplots(figsize=(9, 4.8))
    _panel(axis, table, "Время, с", x="m", scale=1e6, logy=False)
    axis.set(title="Время почти не зависит от длины образца",
             xlabel="Длина образца m", ylabel="Время поиска, мкс")
    figure.tight_layout()
    plt.show()


def plot_found_missing(table: pd.DataFrame) -> None:
    """Присутствующий и отсутствующий образец: по панели на случай.

    Шкала времени у панелей общая, поэтому разница между случаями видна прямо
    по высоте кривых, а не по подписям осей.
    """
    cases = list(table["Случай"].unique())
    figure, axes = plt.subplots(1, len(cases), figsize=(6.5 * len(cases), 4.6),
                                squeeze=False, sharey=True)
    flat = [axis for row in axes for axis in row]
    collected = []
    for axis, case in zip(flat, cases):
        ends = _panel(axis, table[table["Случай"] == case], "Время, с",
                      scale=1e6, headroom=False)
        collected.append((axis, ends))
        axis.set(title=case, xlabel="Длина текста n")
    # Шкала общая, поэтому запас берётся один раз, когда обе панели уже
    # нарисованы: иначе границы считались бы по данным первой из них.
    _headroom(flat[0])
    for axis, ends in collected:
        _annotate_ends(axis, ends)
    flat[0].set_ylabel("Время поиска, мкс")
    figure.suptitle("Образец есть и образца нет   \u00b7   шкала времени общая")
    figure.tight_layout()
    plt.show()


def plot_big_log(table: pd.DataFrame) -> None:
    """Поиск сигнатур в большом журнале: столбик на алгоритм в каждой группе."""
    signatures = list(table["Сигнатура"].unique())
    algorithms = list(table["Алгоритм"].unique())
    width = 0.8 / len(algorithms)
    positions = range(len(signatures))

    figure, axis = plt.subplots(figsize=(10, 4.8))
    top = 0.0
    for index, name in enumerate(algorithms):
        part = table[table["Алгоритм"] == name].set_index("Сигнатура").loc[signatures]
        heights = part["Время, с"] * 1e6
        top = max(top, float(heights.max()))
        axis.bar([position + index * width for position in positions],
                 heights, width=width, label=name)
    axis.set_xticks([position + 0.4 - width / 2 for position in positions])
    axis.set_xticklabels(signatures, rotation=12, fontsize=9)
    axis.set_ylim(0, top * 1.28)
    axis.set(ylabel="Время поиска, мкс", title="Поиск сигнатур в большом журнале")
    axis.grid(True, axis="y", alpha=0.25)
    # Легенда полосой поверх столбиков: сбоку она накрыла бы крайний столбик.
    axis.legend(fontsize=8, ncol=len(algorithms), loc="upper center")
    figure.tight_layout()
    plt.show()
