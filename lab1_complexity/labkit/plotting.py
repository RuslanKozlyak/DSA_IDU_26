"""Графики работы 1.

Каждый эксперимент даёт одну фигуру. Панели внутри неё строятся по общей
сетке и различаются ровно одним: что именно отложено по вертикали. Сравнение
делает глаз, а не подпись под картинкой.
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


def _columns(table: pd.DataFrame) -> list[str]:
    return [column for column in table.columns if column != "n"]


def _curves(axis, table, columns=None, scale=1.0, normalize=False,
            logy=True, annotate=False) -> None:
    """Кривые по столбцам таблицы; `normalize` делит серию на её первое значение."""
    points = [int(n) for n in table["n"]]
    ends = []
    for index, column in enumerate(columns or _columns(table)):
        values = [float(v) * scale for v in table[column]]
        if normalize and values[0]:
            values = [v / values[0] for v in values]
        axis.plot(points, values, marker=MARKERS[index % len(MARKERS)],
                  markersize=4.5, label=column)
        ends.append((points[-1], values[-1], _number(values[-1])))
    _size_axis(axis, points)
    if logy:
        axis.set_yscale("log")
        _readable_ticks(axis)
    else:
        axis.set_ylim(bottom=0)
    axis.grid(True, which="both", alpha=0.25)
    axis.legend(fontsize=8, loc="upper left")
    _headroom(axis)
    if annotate:
        _annotate_ends(axis, ends)


def _steps(table: pd.DataFrame):
    """Подписи переходов между соседними размерами: `10\u2192100`, `100\u21921k`, ..."""
    points = [int(n) for n in table["n"]]
    return [f"{_tick_label(a)}\u2192{_tick_label(b)}"
            for a, b in zip(points, points[1:])]


def _step_bars(axis, table, kind: str, reference: float, title: str,
               reference_label: str, ylabel: str, logy: bool = False) -> None:
    """Столбики по переходам: во сколько раз или на сколько вырос счёт.

    Класс роста виден по тому, какой из двух столбиков одинаков на всех
    переходах. У линейного поиска постоянно отношение: массив вырос вдесятеро,
    и счёт вырос вдесятеро. У двоичного постоянна разность: каждое
    удесятерение добавляет одни и те же примерно три обращения, потому что
    `log2(10n) - log2(n)` от `n` не зависит.

    Легенды здесь нет намеренно: цвета те же, что на левой панели фигуры, а
    пунктир подписан прямо на своём уровне.
    """
    labels = _steps(table)
    columns = _columns(table)
    width = 0.8 / len(columns)
    positions = range(len(labels))
    top = 0.0
    for index, column in enumerate(columns):
        values = [float(v) for v in table[column]]
        if kind == "ratio":
            heights = [b / a if a else float("nan") for a, b in zip(values, values[1:])]
        else:
            heights = [b - a for a, b in zip(values, values[1:])]
        top = max(top, max(heights))
        axis.bar([p + index * width for p in positions], heights, width=width,
                 label=column)
        for position, height in zip(positions, heights):
            axis.annotate(_number(height), (position + index * width, height),
                          textcoords="offset points", xytext=(0, 3),
                          fontsize=8, ha="center")
    axis.axhline(reference, linestyle="--", linewidth=1.3, color="0.25", zorder=3)
    axis.set_title(f"{title}\n{reference_label}", fontsize=11)
    axis.set_ylabel(ylabel)
    axis.set_xticks([p + 0.4 - width / 2 for p in positions])
    axis.set_xticklabels(labels, fontsize=8.5)
    if logy:
        axis.set_yscale("log")
        _readable_ticks(axis)
    else:
        axis.set_ylim(0, top * 1.18)
    axis.grid(True, axis="y", which="both", alpha=0.25)


def plot_accesses(table: pd.DataFrame) -> None:
    """Число обращений: сам счёт и два способа увидеть его класс роста.

    Левая панель кладёт измеренный счёт поверх теоретических кривых `n` и
    `log2 n`: серые пунктиры видно из-под точек ровно настолько, насколько
    оценка расходится с опытом. Правые две панели показывают, что меняется
    при удесятерении массива. Одинаковая высота столбиков и есть подпись
    класса роста: у линейного поиска одинаковы отношения, у двоичного -
    разности.
    """
    points = [int(n) for n in table["n"]]
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    axes[0].plot(points, points, linestyle="--", linewidth=1.2, color="0.45",
                 zorder=0, label="теория: n")
    axes[0].plot(points, [max(1.0, math.log2(n)) for n in points],
                 linestyle=":", linewidth=1.4, color="0.45", zorder=0,
                 label="теория: log\u2082 n")
    _curves(axes[0], table, annotate=True)
    axes[0].set(title="Число обращений", xlabel="Размер массива n",
                ylabel="Обращений к элементам")

    _step_bars(axes[1], table, "ratio", 10.0, "Во сколько раз вырос счёт",
               "пунктир: сам массив вырос в 10 раз", "Отношение")
    axes[1].set_xlabel("Удесятерение массива")

    _step_bars(axes[2], table, "difference", math.log2(10),
               "На сколько вырос счёт", "пунктир: log\u2082 10 \u2248 3,3",
               "Разность", logy=True)
    axes[2].set_xlabel("Удесятерение массива")

    figure.suptitle("Число обращений при неуспешном поиске"
                    "   \u00b7   постоянная величина и есть класс роста")
    figure.tight_layout()
    plt.show()


def plot_times(table: pd.DataFrame, accesses: pd.DataFrame | None = None) -> None:
    """Время одного поиска и сверка его формы с числом обращений.

    Секундомер и счётчик меряют разное, и совпадать обязаны не значения, а
    форма роста. Поэтому на правых панелях обе величины поделены на своё
    значение при наименьшем `n`: остаётся чистый рост, и видно, повторяет ли
    время предсказание счётчика.
    """
    columns = _columns(table)
    if accesses is None:
        figure, axis = plt.subplots(figsize=(9, 4.8))
        _curves(axis, table, scale=1e6, annotate=True)
        axis.set(title="Время одного поиска", xlabel="Размер массива n",
                 ylabel="Время, мкс")
        figure.tight_layout()
        plt.show()
        return

    figure, axes = plt.subplots(1, 1 + len(columns),
                                figsize=(5.4 * (1 + len(columns)), 4.8))
    _curves(axes[0], table, scale=1e6, annotate=True)
    axes[0].set(title="Время одного поиска", xlabel="Размер массива n",
                ylabel="Время, мкс")

    for axis, column in zip(axes[1:], columns):
        paired = pd.DataFrame({
            "n": table["n"],
            "время": list(table[column]),
            "обращения": list(accesses[column]),
        })
        _curves(axis, paired, normalize=True, annotate=True)
        axis.set(title=column, xlabel="Размер массива n",
                 ylabel="Рост относительно наименьшего n")

    figure.suptitle("Время работы   \u00b7   справа обе величины поделены "
                    "на своё значение при наименьшем n")
    figure.tight_layout()
    plt.show()
