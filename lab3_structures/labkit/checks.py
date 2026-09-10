"""Тесты корректности структур данных работы 3."""

from __future__ import annotations

import random

from .core import Checker
from .diagnostics import case_detail
from .data import anagram_keys, random_string_keys


def _skipped(factory, title: str) -> bool:
    """Заготовка ещё не реализована."""
    try:
        factory()
    except NotImplementedError:
        print(f"{title}: реализация не завершена, тесты пропущены")
        return True
    except Exception:  # noqa: BLE001
        return False
    return False


def _content(structure) -> list:
    return [structure.get(index) for index in range(len(structure))]


_ANY = object()


def _step(checker, name, structure, call, action, expected_state,
          expected_value=_ANY, state=_content):
    """One mutation, with snapshots; never execute the operation twice."""
    try:
        before = state(structure)
    except Exception as error:
        before = f'состояние недоступно: {error!r}'
    inputs = {'before': before, 'call': call}
    if hasattr(structure, 'capacity'):
        inputs['capacity'] = structure.capacity
    def run():
        result = action()
        return {'return': result, 'after': state(structure)}
    expected = {'return': 'не проверяется' if expected_value is _ANY else expected_value,
                'after': expected_state}
    ok = checker.check_call(name, run, inputs=inputs, expected=expected,
                            compare=lambda got: got['after'] == expected_state
                            and (expected_value is _ANY or got['return'] == expected_value))
    if not ok:
        # Stop before another test consumes a corrupted structure and masks
        # the original input/output with an unrelated exception.
        checker.report(verbose=False)
    return ok


def _stack_state(stack):
    empty = stack.is_empty()
    return {'size': len(stack), 'empty': empty,
            'top': None if empty else stack.top()}


def check_fixed_array(array_class, title: str = "Массив фиксированной ёмкости", verbose: bool = True):
    """Проверить массив фиксированной ёмкости, включая неизменность хранилища."""
    if _skipped(lambda: array_class(4), title):
        return None

    checker = Checker(title)
    array = array_class(3)
    checker.check_case("новый массив пуст", {'capacity':3}, len(array), 0)
    _step(checker, 'добавление в конец', array, 'append(10), append(20), append(30)',
          lambda:[array.append(v) for v in (10,20,30)], [10,20,30])
    checker.check_raises("переполнение — ошибка", Exception, array.append, 40,
                         inputs={'before':_content(array),'capacity':3,'call':'append(40)'})

    array = array_class(6)
    _step(checker,'подготовка массива',array,'append(1), append(3)',
          lambda:[array.append(v) for v in (1,3)],[1,3])
    _step(checker,'вставка в середину',array,'insert(1, 2)',lambda:array.insert(1,2),[1,2,3])
    _step(checker,'вставка в начало',array,'insert(0, 0)',lambda:array.insert(0,0),[0,1,2,3])
    _step(checker,'вставка в конец через insert',array,'insert(len(array), 4)',lambda:array.insert(len(array),4),[0,1,2,3,4])
    _step(checker,'удаление из начала',array,'remove_at(0)',lambda:array.remove_at(0),[1,2,3,4],0)
    _step(checker,'удаление с конца',array,'remove_at(len(array)-1)',lambda:array.remove_at(len(array)-1),[1,2,3],4)
    _step(checker,'удаление из середины',array,'remove_at(1)',lambda:array.remove_at(1),[1,3],2)
    checker.check_raises("чтение за границей — ошибка", Exception, array.get, 5,
                         inputs={'before':_content(array),'call':'get(5)'})
    checker.check_raises("удаление за границей — ошибка", Exception, array.remove_at, 5,
                         inputs={'before':_content(array),'call':'remove_at(5)'})

    # Требование: длина внутреннего хранилища после создания не меняется.
    array = array_class(8)
    storage_before = {
        name: len(value) for name, value in vars(array).items() if isinstance(value, list)
    }
    for value in range(5):
        array.append(value)
    array.insert(0, -1)
    array.remove_at(2)
    array.remove_at(0)
    storage_after = {
        name: len(value) for name, value in vars(array).items() if isinstance(value, list)
    }
    checker.check_case("внутреннее хранилище есть", {'capacity':8}, storage_before,
                       'хотя бы одно поле-хранилище',compare=bool)
    checker.check_case(
        "длина внутреннего хранилища не менялась",
        {'before':storage_before,'call':'append(0..4), insert(0,-1), remove_at(2), remove_at(0)'},
        storage_after, storage_before,
    )
    checker.check_case(
        "хранилище создано сразу на всю ёмкость",
        {'capacity':8},storage_before,'длина каждого хранилища равна 8',
        compare=lambda lengths:bool(lengths) and all(length==8 for length in lengths.values()),
    )

    rng = random.Random(3)
    model: list[int] = []
    array = array_class(200)
    failure = None
    for step in range(500):
        before = list(model)
        call, got, expected = 'без изменения', None, None
        try:
            if not model or rng.random() < 0.6:
                if len(model) < 200:
                    index = rng.randint(0, len(model))
                    value = rng.randint(0, 99)
                    call = f'insert({index}, {value})'
                    array.insert(index, value)
                    model.insert(index, value)
            else:
                index = rng.randrange(len(model))
                call = f'remove_at({index})'
                expected = model.pop(index)
                got = array.remove_at(index)
            actual = _content(array)
            if got != expected or actual != model:
                failure = f'seed=3, шаг={step}: ' + case_detail({'before':before,'call':call},
                    {'return':got,'after':actual},{'return':expected,'after':model})
                break
        except Exception as error:
            failure = f'seed=3, шаг={step}: ' + case_detail({'before':before,'call':call},repr(error),model)
            break
    checker.check("500 случайных операций", failure is None, failure or "")

    checker.report(verbose)
    return checker


def check_linked_list(list_class, title: str, verbose: bool = True):
    """Проверить связный список."""
    if _skipped(list_class, title):
        return None

    checker = Checker(title)
    linked = list_class()
    checker.check_case("новый список пуст", 'создание пустого списка', len(linked), 0)
    _step(checker,'добавление в конец',linked,'append(1), append(2), append(3)',
          lambda:[linked.append(v) for v in (1,2,3)],[1,2,3])
    _step(checker,'вставка в начало',linked,'prepend(0)',lambda:linked.prepend(0),[0,1,2,3])
    checker.check_call('доступ по индексу',lambda:(linked.get(0),linked.get(3)),expected=(0,3),
                       inputs={'before':_content(linked),'call':'get(0), get(3)'})
    checker.check_raises("чтение за границей — ошибка", Exception, linked.get, 4,
                         inputs={'before':_content(linked),'call':'get(4)'})
    _step(checker,'удаление первого',linked,'remove_first()',linked.remove_first,[1,2,3],0)

    single = list_class()
    _step(checker,'подготовка одного элемента',single,'append(42)',lambda:single.append(42),[42])
    _step(checker,'удаление единственного элемента',single,'remove_first()',single.remove_first,[],42)
    _step(checker,'список пригоден после опустошения',single,'append(1)',lambda:single.append(1),[1])
    checker.check_raises("удаление из пустого — ошибка", Exception, list_class().remove_first,
                         inputs={'before':[],'call':'remove_first()'})

    rng = random.Random(5)
    model: list[int] = []
    linked = list_class()
    failure = None
    for step in range(500):
        before = list(model)
        call, got, expected = 'без изменения', None, None
        try:
            action = rng.random()
            if action < 0.4:
                value = rng.randint(0, 99)
                call = f'append({value})'
                linked.append(value)
                model.append(value)
            elif action < 0.8:
                value = rng.randint(0, 99)
                call = f'prepend({value})'
                linked.prepend(value)
                model.insert(0, value)
            elif model:
                call = 'remove_first()'
                expected = model.pop(0)
                got = linked.remove_first()
            actual = _content(linked)
            if got != expected or actual != model:
                failure = f'seed=5, шаг={step}: ' + case_detail({'before':before,'call':call},
                    {'return':got,'after':actual},{'return':expected,'after':model})
                break
        except Exception as error:
            failure = f'seed=5, шаг={step}: ' + case_detail({'before':before,'call':call},repr(error),model)
            break
    checker.check("500 случайных операций", failure is None, failure or "")

    checker.report(verbose)
    return checker


def check_hash_functions(hash_sum, hash_poly, title: str = "Хеш-функции",
                         verbose: bool = True):
    """Проверить обе хеш-функции: диапазон, детерминированность, порядок."""
    if _skipped(lambda: hash_sum("a", 8), title) or _skipped(
            lambda: hash_poly("a", 8), title):
        return None

    checker = Checker(title)
    words = random_string_keys(200, seed=3)
    for name, function in (("сумма кодов", hash_sum), ("полиномиальный", hash_poly)):
        values = [function(word, 97) for word in words]
        checker.check(
            f"{name}: значение в диапазоне 0..m-1",
            all(isinstance(v, int) and 0 <= v < 97 for v in values),
        )
        checker.check(
            f"{name}: одинаковый результат при повторном вызове",
            all(function(word, 97) == value for word, value in zip(words, values)),
        )
        checker.check(
            f"{name}: результат зависит от m",
            function(words[0], 97) == function(words[0], 97)
            and function(words[0], 101) < 101,
        )

    checker.check_call('сумма кодов: анаграммы дают один хеш',
                       lambda:[hash_sum(s,13) for s in ('abc','cab','bca')],
                       expected=[8,8,8],inputs={'keys':['abc','cab','bca'],'m':13})
    checker.check_call('полиномиальный: анаграммы попадают в разные слоты',
                       lambda:[hash_poly(s,13) for s in ('abc','cab','bca')],
                       expected='три различных хеша в [0, 12]',
                       compare=lambda values:len(set(values))==3 and all(0<=v<13 for v in values),
                       inputs={'keys':['abc','cab','bca'],'m':13})

    anagrams = anagram_keys(300, seed=5)
    occupied = len({hash_poly(word, 97) for word in anagrams})
    checker.check(
        "полиномиальный: 300 анаграмм занимают почти все 97 слотов",
        occupied >= 80,
        f"занято слотов: {occupied}",
    )

    checker.report(verbose)
    return checker


def check_hash_table(table_class, hash_function, title: str, verbose: bool = True):
    """Проверить операции хеш-таблицы."""
    def probe_implementation():
        table = table_class(4, hash_function)
        table.insert("a", 1)

    if _skipped(probe_implementation, title):
        return None

    checker = Checker(title)
    table = table_class(8, hash_function)
    checker.check_case("новая таблица пуста", {'capacity':8}, len(table), 0)
    checker.check_case("ёмкость доступна", {'capacity':8},getattr(table,'capacity',None),8)
    def insert_read(entries, key):
        for k,v in entries:
            table.insert(k,v)
        return {'find':table.find(key),'size':len(table)}
    checker.check_call('добавление и поиск',insert_read,[('a',1)],'a',
                       inputs={'capacity':8,'call':"insert('a',1), find('a'), len(table)"},
                       expected={'find':1,'size':1})
    checker.check_call('повторный ключ обновляет значение',insert_read,[('a',100)],'a',
                       inputs={'history':[("insert",'a',1)],'call':"insert('a',100), find('a'), len(table)"},
                       expected={'find':100,'size':1})
    checker.check_call('несколько ключей',insert_read,[('b',2),('c',3)],'b',
                       inputs={'history':[("insert",'a',100)],'call':"insert('b',2), insert('c',3), find('b'), len(table)"},
                       expected={'find':2,'size':3})
    checker.check_call('проверка наличия',lambda:(table.contains('b'),table.contains('z')),
                       inputs={'inserted':[('a',100),('b',2),('c',3)],'call':"contains('b'), contains('z')"},
                       expected=(True,False))
    checker.check_call('поиск отсутствующего ключа возвращает None',table.find,'z',
                       inputs={'inserted':[('a',100),('b',2),('c',3)],'call':"find('z')"},
                       expected=None)

    table = table_class(64, hash_function)
    keys = random_string_keys(40, seed=1)
    for key in keys:
        table.insert(key, key * 2)
    checker.check(
        "40 ключей: все значения на месте",
        all(table.find(key) == key * 2 for key in keys) and len(table) == 40,
    )

    # Анаграммы: у суммы кодов все они попадают в один слот, и таблица обязана
    # остаться работоспособной — это и есть проверка разрешения коллизий.
    table = table_class(64, hash_function)
    words = anagram_keys(40, seed=2)
    for word in words:
        table.insert(word, word.upper())
    checker.check(
        "40 анаграмм: все значения на месте",
        all(table.find(word) == word.upper() for word in words) and len(table) == 40,
    )

    small = table_class(8, hash_function)
    inserted = list(enumerate(random_string_keys(8, seed=4)))
    for index, word in inserted:
        small.insert(word, index)
    state = {'capacity':8,'inserted':[(word,index) for index,word in inserted]}
    checker.check_case("таблица заполнена целиком",state,len(small),8)
    if getattr(small, "slots", None) is not None:
        checker.check_raises(
            "вставка в заполненную таблицу — ошибка",
            Exception, small.insert, "zzzz", 0,inputs={**state,'call':"insert('zzzz',0)"},
        )
        checker.check_call(
            "поиск отсутствующего ключа в заполненной таблице завершается",
            small.find,'zzzz',inputs={**state,'call':"find('zzzz')"},
            expected=None,
        )

    table = table_class(128, hash_function)
    rng = random.Random(9)
    alphabet = random_string_keys(50, seed=7)
    model: dict[str, int] = {}
    failure = None
    for step in range(400):
        key = rng.choice(alphabet)
        call, got, expected = '', None, None
        try:
            if rng.random() < 0.7:
                value = rng.randrange(1000)
                call = f'insert({key!r}, {value})'
                table.insert(key, value)
                model[key] = value
            else:
                expected = model.get(key)
                if expected is None:
                    call, expected = f'contains({key!r})', False
                    got = table.contains(key)
                else:
                    call = f'find({key!r})'
                    got = table.find(key)
                if got != expected:
                    failure = f'seed=9, шаг={step}, ключи={alphabet!r}: ' + case_detail({'model':model,'call':call},got,expected)
                    break
        except Exception as error:
            failure = f'seed=9, шаг={step}, ключи={alphabet!r}: ' + case_detail({'model':model,'call':call},repr(error),expected)
            break
    checker.check("400 случайных операций", failure is None, failure or "")
    checker.check("число элементов совпадает", len(table) == len(model))

    checker.report(verbose)
    return checker


def check_stack(factory, title: str, verbose: bool = True):
    """Проверить стек: порядок LIFO и ошибки на пустом стеке."""
    if _skipped(lambda: factory(4), title):
        return None

    checker = Checker(title)
    stack = factory(8)
    checker.check_call('новый стек пуст',stack.is_empty,expected=True,inputs={'capacity':8,'call':'is_empty()'})
    _step(checker,'после push стек не пуст',stack,'push(10)',lambda:stack.push(10),
          {'size':1,'empty':False,'top':10},state=_stack_state)
    _step(checker,'top показывает последний добавленный',stack,'push(20), top()',lambda:stack.push(20),
          {'size':2,'empty':False,'top':20},state=_stack_state)
    _step(checker,'pop возвращает последний добавленный',stack,'pop()',stack.pop,
          {'size':1,'empty':False,'top':10},20,state=_stack_state)
    checker.check_call('top после pop',stack.top,expected=10,
                       inputs={'before':_stack_state(stack),'call':'top()'})
    _step(checker,'последний pop опустошает стек',stack,'pop()',stack.pop,
          {'size':0,'empty':True,'top':None},10,state=_stack_state)
    checker.check_raises("pop из пустого — ошибка", Exception, stack.pop,inputs={'before':[],'call':'pop()'})
    checker.check_raises("top из пустого — ошибка", Exception, stack.top,inputs={'before':[],'call':'top()'})

    stack = factory(200)
    model: list[int] = []
    rng = random.Random(13)
    failure = None
    for step in range(300):
        before = list(model)
        call, expected = 'без изменения', None
        try:
            if not model or rng.random() < 0.6:
                if len(model) < 200:
                    value = rng.randrange(1000)
                    call = f'push({value})'
                    stack.push(value)
                    model.append(value)
            else:
                call = 'pop()'
                expected = model.pop()
                got = stack.pop()
                if got != expected:
                    failure = f'seed=13, шаг={step}: ' + case_detail({'before':before,'call':call},got,expected)
                    break
        except Exception as error:
            failure = f'seed=13, шаг={step}: ' + case_detail({'before':before,'call':call},repr(error),expected)
            break
    checker.check("300 случайных операций", failure is None, failure or "")

    checker.report(verbose)
    return checker
