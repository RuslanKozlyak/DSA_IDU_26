"""Линейные графики полных значений, без нормировки на размер входа."""

import math

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from .scenarios import COMPARISON_SORTS

LABELS = {
    "пузырьковая": "Пузырьковая / Bubble Sort",
    "подсчётом": "Подсчётом / Counting Sort",
    "быстрая": "Быстрая / Quick Sort",
    "слиянием": "Слиянием / Merge Sort",
    "пирамидальная": "Пирамидальная / Heap Sort",
    "поразрядная": "Поразрядная / Radix Sort",
    "блочная": "Блочная / Bucket Sort",
}
COLORS = dict(zip(LABELS, ("#2878b5", "#ee8c22", "#23935c", "#d84343",
                          "#9162b6", "#8c564b", "#ba559e", "#667c27")))
METRICS = ("Сравнений", "Время, с")
TITLES = {"Сравнений": "Число сравнений", "Время, с": "Время, мс"}
def _format(value, _):
    return f"{value:,.0f}".replace(",", " ") if abs(value) >= 1000 else f"{value:g}"


def _axis(ax, metric, xlabel="Размер массива n"):
    ax.set(xlabel=xlabel, ylabel=TITLES[metric], ylim=(0, None))
    ax.yaxis.set_major_formatter(FuncFormatter(_format))
    ax.grid(True, alpha=.23)
    ax.set_axisbelow(True)
    ax.spines[["right", "top"]].set_visible(False)


def _lines(ax, table, metric, *, guides=False):
    scale = 1000 if metric == "Время, с" else 1
    for index, (name, part) in enumerate(table.groupby("Алгоритм", sort=False)):
        label = name.capitalize()
        part = part.sort_values("x")
        color = COLORS.get(name, "gray")
        ax.plot(part["x"], part[metric] * scale, label=label, color=color,
                linewidth=1.8, marker="os^D"[index % 4], markersize=3,
                markevery=max(1, len(part) // 12))
        if metric == "Время, с":
            ax.fill_between(part["x"].to_numpy(),
                            part["Время Q1, с"].to_numpy() * scale,
                            part["Время Q3, с"].to_numpy() * scale,
                            color=color, alpha=.12, linewidth=0)
    if guides and metric == "Сравнений" and not table.empty:
        points = sorted(table["x"].unique())
        ax.plot(points, points, "k:", linewidth=2, label="n (ориентир)")
        ax.plot(points, [n * math.log2(n) for n in points], "--", color=".35",
                linewidth=1.5, label="n · log₂ n (ориентир)")
def _ceiling(table, metric):
    if metric == "Сравнений":
        return 10_000
    fast = table[~table["Алгоритм"].isin(["пузырьковая"])]
    if fast.empty:
        fast = table
    return max(1e-6, float(fast[metric].max()) * 1000 * 1.4)


def _clip(ax, table, metric, ceiling):
    ax.set_ylim(0, ceiling)
    scale = 1000 if metric == "Время, с" else 1
    hidden = table[table[metric] * scale > ceiling]["Алгоритм"].unique()
    if len(hidden):
        names = ", ".join(hidden)
        ax.text(.98, .04, f"↑ Выше шкалы: {names}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8, color="#555555",
                bbox=dict(facecolor="white", alpha=.85, edgecolor="none"))


def _finish(fig, title, table, *, shared_legend=False, fixed_n=False, metric=None):
    samples = int(table["Входов"].iloc[0])
    repeats = int(table["Замеров на вход"].iloc[0])
    fig.suptitle(title, fontsize=15)
    note = (f"n = {int(table['n'].iloc[0])} · размер входа фиксирован\n"
            if fixed_n else
            f"До 512 элементов · без деления на n · сравнения: среднее по {samples} входам\n")
    if metric == "Сравнений":
        note += (f"Сравнения: только между элементами; среднее по {samples} входам; "
                 "прочие операции не учитываются")
    else:
        note += (f"Время: медиана {samples} × {repeats} замеров; прогрев исключён; "
                 "полоса — 25–75-й процентили")
    fig.text(.5, .014, note, ha="center", fontsize=9, color="#526174")
    if shared_legend:
        handles, labels = fig.axes[0].get_legend_handles_labels()
        # Отдельная нижняя область в дюймах: не зависит от числа рядов панелей.
        height = fig.get_figheight()
        fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9,
                   bbox_to_anchor=(.5, .52 / height), frameon=False)
        fig.tight_layout(rect=(0, 1.12 / height, 1, .95))
    else:
        fig.tight_layout(rect=(0, .07, 1, .95))
    plt.show()
    return fig


def plot_overview(table):
    """Все алгоритмы вместе; полная шкала и увеличенный фрагмент тех же кривых."""
    random = table
    if random.empty:
        print("Общее сравнение: нет реализованных сортировок.")
        return []
    figures = []
    for metric in METRICS:
        fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
        for ax in axes:
            _lines(ax, random, metric, guides=True)
            _axis(ax, metric)
            ax.set_xlim(0, 530)
        axes[0].set_title("Полная шкала: все значения")
        axes[1].set_title("Увеличенный фрагмент: те же алгоритмы")
        _clip(axes[1], random, metric, _ceiling(random, metric))
        figures.append(_finish(fig, f"Случайный вход · {TITLES[metric]}", random,
                               shared_legend=True))
    return figures


def _keyspace_figure(table, algorithms, title, work_label):
    """Две строки согласованных панелей: работа сверху, время снизу."""
    columns = len(algorithms)
    fig, axes = plt.subplots(2, columns, figsize=(5.3 * columns, 8.2),
                             squeeze=False, sharex="col")
    ticks = (1, 4, 16, 64, 256, 4096, 65536, 1048576)
    n = int(table["n"].iloc[0])
    for col, name in enumerate(algorithms):
        part = table[table["Алгоритм"] == name].sort_values("x")
        x = part["x"].to_numpy()
        color = COLORS[name]
        for row, (column, scale) in enumerate((("Работа", 1), ("Время, с", 1000))):
            ax = axes[row, col]
            ax.plot(x, part[column] * scale, color=color, linewidth=2.2,
                    marker="o", markersize=4)
            if column == "Время, с":
                ax.fill_between(x, part["Время Q1, с"].to_numpy() * scale,
                                part["Время Q3, с"].to_numpy() * scale,
                                color=color, alpha=.15, linewidth=0)
            _axis(ax, "Время, с" if column == "Время, с" else "Сравнений",
                  "Размер пространства ключей k")
            if row == 0:
                ax.set_ylabel(work_label)
                ax.set_title(name.capitalize())
            ax.set_xscale("log", base=2)
            shown = [tick for tick in ticks if part["x"].min() <= tick <= part["x"].max()]
            ax.set_xticks(shown)
            ax.xaxis.set_major_formatter(FuncFormatter(_format))
            ax.set_xlim(part["x"].min(), part["x"].max())
    samples = int(table["Входов"].iloc[0])
    repeats = int(table["Замеров на вход"].iloc[0])
    fig.suptitle(f"{title} · случайные ключи из [0, k), n = {n}", fontsize=15)
    detail = ("Сверху — сравнения между элементами."
              if work_label == "Число сравнений" else
              "Сверху — выполненные шаги циклов в коде алгоритма и его помощников.")
    fig.text(.5, .018,
             f"{detail} Один шаг цикла не равен одной машинной операции.\n"
             f"Снизу — время: медиана {samples} × {repeats} замеров; "
             "прогрев исключён; полоса — 25–75-й процентили.",
             ha="center", fontsize=9, color="#526174")
    fig.tight_layout(rect=(0, .08, 1, .95))
    plt.show()
    return fig


def plot_keyspace(table):
    """Раздельные пары графиков для сравнительных и распределительных сортировок."""
    if table.empty:
        print("Пространство ключей: нет результатов.")
        return []
    present = set(table["Алгоритм"])
    comparison = [name for name in LABELS if name in present and name in COMPARISON_SORTS]
    distribution = [name for name in LABELS if name in present and name not in COMPARISON_SORTS]
    figures = []
    if comparison:
        figures.append(_keyspace_figure(
            table, comparison, "Сортировки на сравнениях", "Число сравнений",
        ))
    if distribution:
        figures.append(_keyspace_figure(
            table, distribution, "Сортировки, основанные на распределении",
            "Шагов циклов",
        ))
    return figures
