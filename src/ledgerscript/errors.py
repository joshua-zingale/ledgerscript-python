import typing as t
_T = t.TypeVar("_T", bound=Exception)

_P = t.ParamSpec("_P")
_U = t.TypeVar("_U")
class ErrorInFile[_T](Exception):
    def __init__(self, source: str, span: tuple[int, int], exception: _T) -> None:
        self.line_number = source[:span[0]].count("\n")
        self.column = next(map(lambda x: x[0], filter(lambda c: c[1] == "\n", enumerate(reversed(source[:span[0]])))), span[0])
        self.str_slice = source[span[0]:span[1]]
        super().__init__(f"line {self.line_number+1} at character {self.column+1}: {exception}")


def cast_to_file_error[**P, R](source: str, span: tuple[int, int], exeptions: tuple[t.Type[Exception],...] | t.Type[Exception], f: t.Callable[P, R], /, *args: P.args, **kwargs: P.kwargs) -> R:
    return cast_exception(lambda x: ErrorInFile(source, span, x), exeptions, f, *args, **kwargs)
    

def cast_exception(caster: t.Callable[[_T], Exception], exeptions: tuple[t.Type[_T], ...] | t.Type[_T], f: t.Callable[_P, _U], /, *args: _P.args, **kwargs: _P.kwargs) -> _U:
    try:
        r = f(*args, **kwargs)
        return r
    except exeptions as e:
        raise caster(e)

