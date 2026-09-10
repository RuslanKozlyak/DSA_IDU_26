"""Readable input / actual output / expected output for short checks."""
import reprlib

_UNSET = object()
_repr = reprlib.Repr()
_repr.maxlist = 24
_repr.maxtuple = 12
_repr.maxdict = 12
_repr.maxstring = 220
_repr.maxother = 180
_repr.maxlevel = 6


def compact(value):
    text = _repr.repr(value)
    return text if len(text) <= 1200 else text[:1197] + '...'


def case_detail(inputs, output, expected):
    return f'Input: {compact(inputs)}\nOutput: {compact(output)}\nExpected: {compact(expected)}'


class Checker:
    """Keep legacy results tuples, with explicit diagnostics for short cases."""
    def __init__(self, title):
        self.title = title
        self.results = []

    def check(self, name, condition, detail=''):
        ok = bool(condition)
        self.results.append((name, ok, detail))
        return ok

    def check_case(self, name, inputs, output, expected, compare=None):
        try:
            ok = bool(compare(output) if compare is not None else output == expected)
        except Exception:
            ok = False
        return self.check(name, ok, case_detail(inputs, output, expected))

    def check_call(self, name, func, *args, expected=None, compare=None, inputs=_UNSET):
        # Render before execution: an in-place algorithm must not rewrite Input.
        input_text = compact(args if inputs is _UNSET else inputs)
        try:
            got = func(*args)
        except NotImplementedError as error:
            raise NotImplementedError(
                f'{error}\nInput: {input_text}\nOutput: NotImplementedError\nExpected: {compact(expected)}') from error
        except Exception as error:
            detail = f'Input: {input_text}\nOutput: {type(error).__name__}: {error}\nExpected: {compact(expected)}'
            return self.check(name, False, detail)
        try:
            ok = bool(compare(got) if compare is not None else got == expected)
        except Exception:
            ok = False
        return self.check(name, ok,
                          f'Input: {input_text}\nOutput: {compact(got)}\nExpected: {compact(expected)}')

    def check_raises(self, name, error_type, func, *args, inputs=_UNSET):
        if inputs is _UNSET:
            inputs = {'call': getattr(func, '__name__', type(func).__name__), 'args': args}
        input_text = compact(inputs)
        expected = error_type.__name__
        try:
            result = func(*args)
        except error_type as error:
            return self.check(name, True,
                              f'Input: {input_text}\nOutput: {type(error).__name__}: {error}\nExpected: исключение {expected}')
        except Exception as error:
            return self.check(name, False,
                              f'Input: {input_text}\nOutput: {type(error).__name__}: {error}\nExpected: исключение {expected}')
        return self.check(name, False,
                          f'Input: {input_text}\nOutput: {compact(result)} (без исключения)\nExpected: исключение {expected}')

    def report(self, verbose=True):
        passed = sum(ok for _, ok, _ in self.results)
        total = len(self.results)
        print(self.title)
        for name, ok, detail in self.results:
            if ok and not verbose:
                continue
            print(f"  {'[ok]  ' if ok else '[FAIL]'} {name}")
            if detail and (not ok or detail.startswith('Input:')):
                for line in detail.splitlines():
                    print('    ' + line)
        print(f'  Пройдено {passed} из {total}')
        if passed != total:
            raise AssertionError(f'{self.title}: не пройдено {total-passed} тестов из {total}. Эксперименты запускать рано.')
        return True
