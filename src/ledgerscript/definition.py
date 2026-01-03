import bisect
import enum
from dataclasses import dataclass
import functools
import re
import typing as t

from .parsing import Production, BinOp, UnaryOp, parse_expression


class RedifinitionError(RuntimeError):
    def __init__(self, redefined_names: t.Sequence[t.Sequence["Definition"]]) -> None:
        assert redefined_names
        super().__init__(
            f"The following name{'s' if len(redefined_names) > 1 else ''} have multiple definitions: {','.join(map(lambda x: x[0].name, redefined_names))}"
        )
        self.redefined_names = redefined_names


class CircularDefinitionError(RuntimeError):
    def __init__(self, affected_definitions: t.Collection[str]) -> None:
        assert len(affected_definitions) > 1
        super().__init__(
            f"The following names are involved in a circular definition: {','.join(map(lambda x: x, affected_definitions))}"
        )
        self.redefined_affected_definitionsnames = affected_definitions


class MissingDefinitionError(RuntimeError):
    def __init__(self, undefined_names: t.Collection[str]) -> None:
        assert len(undefined_names) > 1
        super().__init__(
            f"The following names are undefined: {','.join(map(lambda x: x, undefined_names))}"
        )
        self.undefined_names = undefined_names


def resolve_definitions(definitions: list["Definition"]) -> dict[str, float]:
    names = set(map(lambda d: d.name, definitions))
    if len(names) < len(definitions):
        name_to_definitions: dict[str, list[Definition]] = {}
        for definition in definitions:
            name_to_definitions[definition.name] = name_to_definitions.get(
                definition.name, []
            ) + [definition]
        raise RedifinitionError(
            list(
                map(
                    lambda x: x[1],
                    filter(lambda x: len(x[1]) > 1, name_to_definitions.items()),
                )
            )
        )

    name_to_definition = {definition.name: definition for definition in definitions}

    last_num_defined_names: int = -1
    defined_names: set[str] = set()
    namespace: dict[str, float] = {}
    while len(names) > len(defined_names):
        if last_num_defined_names == len(defined_names):
            raise CircularDefinitionError(names - defined_names)
        last_num_defined_names = len(defined_names)
        for undefined_name in filter(
            lambda n: not name_to_definition[n].dependencies - defined_names,
            names - defined_names,
        ):
            namespace[undefined_name] = eval(
                name_to_definition[undefined_name].production, namespace
            )
            defined_names.add(undefined_name)

    if undefined_names := names - defined_names:
        raise MissingDefinitionError(undefined_names)

    assert set(namespace) == names
    return namespace


expression_regex = re.compile(r"@=([a-zA-Z](?:[a-zA-Z\d_]*[a-zA-Z\d])?)\[([^\]]*)\]")


def get_definitions(source: str) -> list["Definition"]:
    definitions = list(
        map(
            lambda x: Definition(
                span=x.span(),
                name=x.groups()[0],
                production=parse_expression(x.groups()[1]),
            ),
            expression_regex.finditer(source),
        )
    )
    return definitions


@dataclass(frozen=True)
class Definition:
    span: tuple[int, int]
    name: str
    production: Production

    @functools.cached_property
    def dependencies(self):
        return get_dependencies(self.production)


class ReferenceDirection(enum.Enum):
    LEFT = 1
    RIGHT = 2


@dataclass
class Reference:
    span: tuple[int, int]
    direction: ReferenceDirection


@dataclass
class ResolvedReference:
    span: tuple[int, int]
    name: str


reference_regex = re.compile(r"@[<>]")


def get_references(source: str) -> list[Reference]:
    return list(
        map(
            lambda x: Reference(
                span=x.span(),
                direction=ReferenceDirection.LEFT
                if "<" in x.group()
                else ReferenceDirection.RIGHT,
            ),
            reference_regex.finditer(source),
        )
    )


def resolve_references(
    references: list[Reference], definitions: list[Definition]
) -> list[ResolvedReference]:
    definitions = sorted(definitions, key=lambda x: x.span[0])

    return list(
        map(
            lambda x: ResolvedReference(
                x.span,
                name=definitions[
                    (
                        bisect.bisect_left(
                            definitions, x.span[0], key=lambda d: d.span[0]
                        )
                        - (1 if x.direction == ReferenceDirection.LEFT else 0)
                    )
                    % len(definitions)
                ].name,
            ),
            references,
        )
    )


class UndefinedNameError(ValueError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Invalid name '{name}'")
        self.name = name


def eval(production: Production, namespace: dict[str, float]) -> float:
    match production:
        case float(num) | int(num):
            return num
        case str(name):
            if name not in namespace:
                raise UndefinedNameError(name)
            return namespace[name]
        case BinOp(op=operator, left=left, right=right):
            return operator(eval(left, namespace), eval(right, namespace))
        case UnaryOp(op=operator, arg=arg):
            return operator(eval(arg, namespace))


def get_dependencies(production: Production) -> set[str]:
    match production:
        case float() | int():
            return set()
        case str(name):
            return set([name])
        case BinOp(left=left, right=right):
            return get_dependencies(left).union(get_dependencies(right))
        case UnaryOp(arg=arg):
            return get_dependencies(arg)
