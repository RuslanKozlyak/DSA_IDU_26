"""Raw-value paired plots; no normalization or fitted reference curves."""
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from .scenarios import CASES

COLORS = {"Линейный поиск":"#2878b5", "Двоичный поиск":"#ee8c22"}


def _format(value, _):
    return f"{value:,.0f}".replace(",", " ") if abs(value)>=1000 else f"{value:g}"


def _lines(ax, table, metric, guides=False):
    scale = 1e6 if metric == "Время, с" else 1
    for j, (name, part) in enumerate(table.groupby("Алгоритм", sort=False)):
        part = part.sort_values("n")
        color = COLORS.get(name, f'C{j}')
        ax.plot(part['n'],part[metric]*scale,label=name,color=color,
                marker='os'[j%2],markersize=3,linewidth=1.8)
        if metric == 'Время, с':
            ax.fill_between(part['n'].to_numpy(),part['Время Q1, с'].to_numpy()*scale,
                            part['Время Q3, с'].to_numpy()*scale,color=color,alpha=.13,linewidth=0)
    if guides and metric=='Обращений':
        points=sorted(table['n'].unique())
        ax.plot(points, points, ':', color='.4', label='n — ориентир')
        ax.plot(points, [math.log2(n) for n in points], '--',color='.55',label='log₂ n — ориентир')
    ax.set(xlabel='Размер массива n', ylabel='Время, мкс' if metric=='Время, с' else 'Обращений к массиву',
           ylim=(0,None), xlim=(0,table['n'].max()*1.04))
    ax.xaxis.set_major_formatter(FuncFormatter(_format))
    ax.yaxis.set_major_formatter(FuncFormatter(_format))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5,integer=True))
    ax.grid(alpha=.22)
    ax.spines[['top','right']].set_visible(False)


def _finish(fig, title):
    fig.suptitle(title,fontsize=17,y=.985)
    entries={}
    for ax in fig.axes:
        handles,labels=ax.get_legend_handles_labels()
        entries.update(zip(labels,handles))
    fig.legend(entries.values(),entries.keys(),loc='lower center',bbox_to_anchor=(.5,.065),ncol=4,frameon=False)
    fig.text(.5,.025,'Полные значения, линейные оси · время: медиана 7 замеров пачками без счётчика; прогрев исключён\n'
             'Полоса — 25–75-й процентили; обращения считаются отдельным запуском; создание массива не учитывается',
             ha='center',fontsize=9,color='#526174')
    fig.tight_layout(rect=(0,.13,1,.94))
    plt.show()
    return fig


def plot_search_overview(table):
    if table.empty:
        print('Нет реализованных алгоритмов')
        return None
    part=table[table['Сценарий']==CASES[3]]
    fig,axes=plt.subplots(2,2,figsize=(15,9))
    binary=part[part['Алгоритм']=='Двоичный поиск']
    for row,metric in enumerate(['Время, с','Обращений']):
        for col in range(2):
            _lines(axes[row,col],part,metric,guides=True)
            axes[row,col].set_title('Общая шкала' if col==0 else 'Увеличенный фрагмент тех же данных')
        if not binary.empty:
            scale=1e6 if row==0 else 1
            ceiling=float(binary['Время Q3, с' if row==0 else metric].max())*scale*1.35
            axes[row,1].set_ylim(0,max(ceiling,1))
            hidden=part[part[metric]*scale>ceiling]['Алгоритм'].unique()
            if len(hidden):
                axes[row,1].text(.03,.92,'Выше шкалы: '+', '.join(hidden),transform=axes[row,1].transAxes,fontsize=9,
                                  bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
    return _finish(fig,'Неуспешный поиск · время и обращения')


def plot_search_positions(table):
    if table.empty:
        print('Нет реализованных алгоритмов')
        return None
    position_cases=CASES[:3]
    fig,axes=plt.subplots(2,len(position_cases),figsize=(16,9))
    for col,case in enumerate(position_cases):
        for row,metric in enumerate(['Время, с','Обращений']):
            _lines(axes[row,col],table[table['Сценарий']==case],metric)
            axes[row,col].set_title(case)
    return _finish(fig,'Позиция искомого элемента · шкалы панелей индивидуальные')
