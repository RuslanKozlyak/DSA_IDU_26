"""Timing plots with quartile bands and shared legends."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

COLORS={'наивный':'#2878b5','Кнут–Моррис–Пратт':'#ee8c22','Рабин–Карп':'#23935c'}

# Подпись оси x зависит от сценария: в одной фигуре колонки могут показывать
# рост разных величин.
X_LABELS = {'Растёт длина текста n': 'Длина текста n',
            'Растёт длина образца m': 'Длина образца m'}


def _format(value, _):
    return f'{value:,.0f}'.replace(',',' ') if abs(value)>=1000 else f'{value:g}'


def _axis(ax, ylabel, xlabel):
    ax.set(xlabel=xlabel,ylabel=ylabel,ylim=(0,None))
    ax.grid(alpha=.22)
    ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)
    ax.yaxis.set_major_formatter(FuncFormatter(_format))


def _finish(fig, table, title, scales='Шкалы панелей индивидуальные.'):
    fig.suptitle(title,fontsize=16,y=.985)
    handles,labels=fig.axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.065),
               ncol=min(4,len(labels)),frameon=False)
    inputs=sorted(table['Входов'].unique())
    count='/'.join(str(v) for v in inputs)
    fig.text(.5,.025,f'Время: медиана {count} × 7 замеров; прогрев исключён; '
             f'полоса — 25–75-й процентили. {scales}',
             ha='center',fontsize=9,color='#526174')
    fig.tight_layout(rect=(0,.13,1,.94))
    plt.show()
    return fig


def plot_search_experiment(table, title, xlabel=None):
    if table.empty:
        print('Нет реализованных алгоритмов — эксперимент пропущен')
        return None
    cases=list(table['Сценарий'].unique())
    fig,axes=plt.subplots(1,len(cases),figsize=(max(10,7.5*len(cases)),5.8),squeeze=False)
    for col,case in enumerate(cases):
        part=table[table['Сценарий']==case]
        ax=axes[0,col]
        for j,(name,values) in enumerate(part.groupby('Алгоритм',sort=False)):
            values=values.sort_values('x')
            color=COLORS.get(name,f'C{j}')
            ax.plot(values['x'],values['Время, с']*1000,label=name[:1].upper()+name[1:],
                    color=color,marker='os^'[j%3],markersize=4,linewidth=1.8)
            ax.fill_between(values['x'].to_numpy(),values['Время Q1, с'].to_numpy()*1000,
                            values['Время Q3, с'].to_numpy()*1000,color=color,alpha=.13,linewidth=0)
        _axis(ax,'Время, мс',xlabel or X_LABELS.get(case,'Размер входа'))
        ax.set_title(case)
        ax.set_xlim(0,part['x'].max()*1.04)
        ax.xaxis.set_major_formatter(FuncFormatter(_format))
        ax.xaxis.set_major_locator(MaxNLocator(nbins=6,integer=True))
    return _finish(fig,table,title)


def plot_log_experiment(table):
    if table.empty:
        print('Нет реализованных алгоритмов — эксперимент пропущен')
        return None
    signatures=list(table['Сценарий'].unique())
    algorithms=list(table['Алгоритм'].unique())
    fig,axes=plt.subplots(1,1,figsize=(12,5.8),squeeze=False)
    width=.8/len(algorithms)
    x=np.arange(len(signatures))
    ax=axes[0,0]
    for j,name in enumerate(algorithms):
        part=table[table['Алгоритм']==name].set_index('Сценарий').loc[signatures]
        y=part['Время, с'].to_numpy()*1000
        error=np.vstack((y-part['Время Q1, с'].to_numpy()*1000,
                         part['Время Q3, с'].to_numpy()*1000-y))
        ax.bar(x-.4+width/2+j*width,y,width,label=name[:1].upper()+name[1:],
               color=COLORS.get(name,f'C{j}'),yerr=error,capsize=3)
    _axis(ax,'Время, мс','Сигнатура')
    ax.set_xticks(x,signatures)
    return _finish(fig,table,'Поиск сигнатур в большом журнале')


def plot_scaling(table):
    """По столбцу на алгоритм: полное время и время на символ."""
    if table.empty:
        print('Нет реализованных алгоритмов — эксперимент пропущен')
        return None
    present = list(table['Алгоритм'].unique())
    preferred = ['наивный', 'Рабин–Карп', 'Кнут–Моррис–Пратт']
    algorithms = [name for name in preferred if name in present]
    algorithms.extend(name for name in present if name not in algorithms)
    fig, axes = plt.subplots(2, len(algorithms),
                             figsize=(max(11, 6.2 * len(algorithms)), 9),
                             squeeze=False, sharex='col')
    colors = ['#2878b5', '#d95f43', '#23935c']
    markers = ['o', 's', '^']
    for col, name in enumerate(algorithms):
        algorithm = table[table['Алгоритм'] == name]
        groups = [(index, case, values.sort_values('n + m'))
                  for index, (case, values)
                  in enumerate(algorithm.groupby('Сценарий', sort=False))]
        for row, (metric, q1, q3, scale) in enumerate((
                ('Время, с', 'Время Q1, с', 'Время Q3, с', 1000),
                ('Время на символ, с', 'Время на символ Q1, с',
                 'Время на символ Q3, с', 1e9))):
            for index, case, values in groups:
                color=colors[index % len(colors)]
                style = dict(color=color, marker=markers[index % len(markers)],
                             markersize=5, linewidth=2, label=case)
                axes[row, col].plot(values['n + m'], values[metric] * scale, **style)
                axes[row, col].fill_between(
                    values['n + m'].to_numpy(), values[q1].to_numpy() * scale,
                    values[q3].to_numpy() * scale, color=color, alpha=.13, linewidth=0)
        axes[0, col].set_title(name[:1].upper() + name[1:])
        for row, ylabel in enumerate(('Время, мс', 'Время на символ, нс')):
            axis = axes[row, col]
            axis.set_ylim(0, None)
            axis.grid(alpha=.22)
            axis.set_axisbelow(True)
            axis.spines[['top', 'right']].set_visible(False)
            axis.xaxis.set_major_formatter(FuncFormatter(_format))
            axis.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
            axis.yaxis.set_major_formatter(FuncFormatter(_format))
            if col == 0:
                axis.set_ylabel(ylabel)
        axes[1, col].set_xlabel('Суммарная длина n + m')
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.suptitle('Масштабирование алгоритмов поиска', fontsize=16, y=.985)
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .055),
               ncol=3, frameon=False)
    ratio = int(round((table['n'] / table['m']).median()))
    fig.text(.5, .015,
             f'Во всех точках m = n / {ratio}; n и m удваиваются вместе. '
             'Нижний ряд показывает медианное время, делённое на n + m. '
             'Шкалы столбцов индивидуальные.',
             ha='center', fontsize=9, color='#526174')
    fig.tight_layout(rect=(0, .12, 1, .94))
    plt.show()
    return fig
