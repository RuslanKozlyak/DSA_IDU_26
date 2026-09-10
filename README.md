# Лабораторные работы по алгоритмам и структурам данных

В репозитории находятся четыре лабораторные работы. Каждая работа выполняется в отдельном Jupyter Notebook и сдаётся отдельным Pull Request.

| Работа | Тема | Ноутбук |
|---|---|---|
| 1 | Анализ сложности алгоритмов | `lab1_complexity/lab1.ipynb` |
| 2 | Алгоритмы сортировки | `lab2_sorting/lab2.ipynb` |
| 3 | Структуры данных и хеширование | `lab3_structures/lab3.ipynb` |
| 4 | Алгоритмы поиска подстроки | `lab4_strings/lab4.ipynb` |

## Подготовка

Нужны Python 3.10 или новее, Git и аккаунт GitHub.

1. Нажмите **Fork** на странице этого репозитория.
2. Клонируйте свой fork, подставив свой логин GitHub:

```bash
git clone https://github.com/ВАШ_ЛОГИН/DSA_IDU_26.git
cd DSA_IDU_26
```

3. Добавьте исходный репозиторий преподавателя:

```bash
git remote add upstream https://github.com/RuslanKozlyak/DSA_IDU_26.git
```

4. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Linux и macOS:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

5. Запустите Jupyter:

```bash
jupyter lab
```

## Выполнение и сдача работы

Каждая лабораторная выполняется в своей ветке. Например, для первой работы:

```bash
git checkout main
git pull upstream main
git checkout -b lab1
```

Откройте соответствующий `labN.ipynb`, реализуйте задания, выполните все ячейки и сохраните ноутбук вместе с результатами проверок и графиками.

Добавляйте в коммит только ноутбук текущей работы:

```bash
git add lab1_complexity/lab1.ipynb
git commit -m "Выполнена лабораторная работа 1"
git push -u origin lab1
```

После push откройте Pull Request:

- **base repository:** `RuslanKozlyak/DSA_IDU_26`;
- **base branch:** `main`;
- **head repository:** ваш fork;
- **compare branch:** `lab1`.

Для следующих работ используйте ветки `lab2`, `lab3` и `lab4`, каждый раз создавая новую ветку от актуального `main`.

## Правила Pull Request

- Один PR содержит ровно одну лабораторную работу.
- Меняется только `labN.ipynb` этой работы.
- Файлы `labkit`, workflow и служебные файлы изменять нельзя.
- В описании PR укажите имя, группу и номер работы.
- Исправления отправляйте новыми коммитами в ту же ветку: открытый PR обновится автоматически.
- Проверенный PR может быть закрыт преподавателем без слияния. Это нормально: решения не должны попадать в `main`.

Автоматическая проверка выполняет код до экспериментальной части ноутбука и запускает встроенные короткие тесты. Эксперименты и графики преподаватель проверяет по сохранённым результатам в ноутбуке.

## Как получить обновления курса

```bash
git checkout main
git fetch upstream
git merge upstream/main
git push origin main
```

Не продолжайте следующую работу в ветке предыдущей лабораторной.
