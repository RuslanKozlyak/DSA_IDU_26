"""Графики работы 3.

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


def _grid(count: int):
    """Сетка панелей: не длиннее двух в высоту, не шире двух в ширину."""
    if count <= 1:
        return 1, 1
    if count == 2:
        return 1, 2
    if count <= 4:
        return 2, 2
    return 2, (count + 1) // 2


def _panel(axis, table, value, series="Структура", x="n", scale=1.0,
           per_element=False, logy=True, annotate=False,
           headroom: bool = True) -> None:
    """Одна панель: кривые по сериям на общей сетке."""
    names = list(table[series].unique())
    points = sorted({int(v) for v in table[x]})
    ends = []
    for index, name in enumerate(names):
        part = table[table[series] == name].sort_values(x)
        values = part[value] / part["n"] * scale if per_element else part[value] * scale
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


def plot_operations(table: pd.DataFrame) -> None:
    """Четыре операции, по панели на операцию, структуры — кривые внутри панели.

    Шкала времени у всех панелей общая, поэтому дешёвая операция и дорогая
    видны в одном масштабе: у операции за `O(1)` кривая горизонтальна, у
    операции за `O(n)` поднимается вместе с размером структуры.
    """
    operations = list(table["Операция"].unique())
    rows, columns = _grid(len(operations))
    figure, axes = plt.subplots(rows, columns, figsize=(6.2 * columns, 4.3 * rows),
                                squeeze=False, sharey=True)
    flat = [axis for row in axes for axis in row]
    for axis, operation in zip(flat, operations):
        _panel(axis, table[table["Операция"] == operation], "Время, с",
               scale=1e6, headroom=False)
        axis.set(title=operation, xlabel="Число элементов n")
    # Шкала общая, поэтому запас берётся один раз, когда все панели уже
    # нарисованы: иначе границы считались бы по данным первой из них.
    _headroom(flat[0])
    for axis in flat[len(operations):]:
        axis.set_visible(False)
    for row in axes:
        row[0].set_ylabel("Время одной операции, мкс")
    figure.suptitle("Время операций   \u00b7   шкала времени у всех панелей общая")
    figure.tight_layout()
    plt.show()


def _ratios(part: pd.DataFrame):
    """Отношения времени соседних размеров там, где размер удвоился."""
    part = part.sort_values("n")
    points = [int(n) for n in part["n"]]
    values = [float(v) for v in part["Время, с"]]
    labels, heights = [], []
    for index in range(1, len(points)):
        if points[index] != 2 * points[index - 1] or not values[index - 1]:
            continue
        labels.append(f"{_tick_label(points[index - 1])}\u2192{_tick_label(points[index])}")
        heights.append(values[index] / values[index - 1])
    return labels, heights


def plot_doubling(table: pd.DataFrame) -> None:
    """Тест удвоения: во сколько раз растёт время при удвоении размера.

    Размер структуры растёт вдвое, поэтому отношение соседних значений времени
    прямо даёт порядок роста: около `1` у операции за `O(1)` и около `2` у
    операции за `O(n)`. Одно отношение может выпасть из-за посторонней нагрузки
    на машину — смотреть надо на весь ряд сразу.
    """
    operations = list(table["Операция"].unique())
    rows, columns = _grid(len(operations))
    figure, axes = plt.subplots(rows, columns, figsize=(6.2 * columns, 4.3 * rows),
                                squeeze=False, sharey=True)
    flat = [axis for row in axes for axis in row]
    for axis, operation in zip(flat, operations):
        part = table[table["Операция"] == operation]
        names = list(part["Структура"].unique())
        labels = []
        for index, name in enumerate(names):
            labels, heights = _ratios(part[part["Структура"] == name])
            axis.plot(range(len(heights)), heights,
                      marker=MARKERS[index % len(MARKERS)], markersize=4.5,
                      label=str(name))
        for level, note in ((1.0, "O(1)"), (2.0, "O(n)")):
            axis.axhline(level, linestyle="--", linewidth=1.2, color="0.45", zorder=0)
            axis.text(0.995, level, note, transform=axis.get_yaxis_transform(),
                      ha="right", va="bottom", fontsize=8.5, color="0.35")
        axis.set_xticks(range(len(labels)))
        axis.set_xticklabels(labels, fontsize=8, rotation=20)
        axis.set_ylim(0, 3)
        axis.set(title=operation, xlabel="Удвоение размера")
        axis.grid(True, axis="y", alpha=0.25)
        axis.legend(fontsize=8, loc="upper left")
    for axis in flat[len(operations):]:
        axis.set_visible(False)
    for row in axes:
        row[0].set_ylabel("Во сколько раз выросло время")
    figure.suptitle("Тест удвоения   \u00b7   отношение около 1 - это O(1), "
                    "около 2 - это O(n)")
    figure.tight_layout()
    plt.show()


def plot_hash_grid(table: pd.DataFrame, title: str | None = None) -> None:
    """Доля коллизий и время поиска для двух хеш-функций."""
    time_panels = (
        ("Время успешного поиска, с", "Время успешного поиска Q1, с",
         "Время успешного поиска Q3, с", "Успешный поиск"),
        ("Время неуспешного поиска, с", "Время неуспешного поиска Q1, с",
         "Время неуспешного поиска Q3, с", "Неуспешный поиск"),
    )
    figure, axes = plt.subplots(1, 3, figsize=(18, 5.4), squeeze=False)
    flat = [axis for row in axes for axis in row]

    collision_axis = flat[0]
    for index, name in enumerate(table["Хеш"].unique()):
        part = (table[table["Хеш"] == name]
                .sort_values("Заполненность α")
                .drop_duplicates("Заполненность α"))
        collision_axis.plot(
            part["Заполненность α"], part["Доля ключей с коллизией"],
            marker=MARKERS[index % len(MARKERS)], markersize=4.5,
            color=f"C{index}", label=str(name),
        )
    collision_axis.set(
        xlabel="Коэффициент заполнения α",
        ylabel="Доля ключей с коллизией",
        title="Коллизии хеш-функции",
    )
    collision_axis.set_ylim(0, 1)
    collision_axis.grid(True, alpha=0.25)
    collision_axis.legend(fontsize=8, loc="upper left")

    for axis, (column, q1, q3, panel_title) in zip(flat[1:], time_panels):
        names = list(table["Вариант"].unique())
        for index, name in enumerate(names):
            part = table[table["Вариант"] == name].sort_values("Заполненность α")
            color = f"C{index}"
            axis.plot(part["Заполненность α"], part[column] * 1e6,
                      marker=MARKERS[index % len(MARKERS)], markersize=4.5,
                      color=color, label=str(name))
            axis.fill_between(part["Заполненность α"].to_numpy(),
                              part[q1].to_numpy() * 1e6,
                              part[q3].to_numpy() * 1e6,
                              color=color, alpha=.13, linewidth=0)
        axis.set(xlabel="Коэффициент заполнения \u03b1",
                 ylabel="Время одного поиска, мкс", title=panel_title)
        axis.set_ylim(bottom=0)
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=8, loc="upper left")
        _headroom(axis)
    ceiling = max(axis.get_ylim()[1] for axis in flat[1:])
    for axis in flat[1:]:
        axis.set_ylim(0, ceiling)
    data = table["Данные"].iloc[0] if "Данные" in table else ""
    figure.suptitle(title or f"Хеш-таблица: {data}")
    figure.tight_layout()
    plt.show()
