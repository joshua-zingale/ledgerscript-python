import itertools
from collections import Counter
from dataclasses import dataclass
import typing as t
from pathlib import Path

from .definition import (
    get_definitions,
    get_references,
    resolve_definitions,
    resolve_references,
    Definition,
    ResolvedReference,
)


@dataclass
class SourceFile:
    content: str
    path: Path | t.Literal["-"]


@dataclass
class ObjFile:
    content: str
    path: Path | t.Literal["-"]
    definitions: list[Definition]
    resolved_references: list[ResolvedReference]


@dataclass
class CompiledFile:
    content: str
    path: Path | t.Literal["-"]


def compile_source(source_file: SourceFile) -> ObjFile:
    definitions = get_definitions(source_file.content)
    references = get_references(source_file.content)
    resolved_references = resolve_references(references, definitions)
    return ObjFile(
        content=source_file.content,
        path=source_file.path,
        definitions=definitions,
        resolved_references=resolved_references,
    )


def compile_str(source: str) -> str:
    obj_file = compile_source(SourceFile(content=source, path="-"))
    namespace = resolve_definitions(obj_file.definitions)
    return compile_obj(obj_file, namespace)


class CrossFileRedefinitionError(RuntimeError):
    def __init__(self, redefined_names: t.Collection[str]) -> None:
        assert redefined_names
        super().__init__(
            f"The following name{'s' if len(redefined_names) > 1 else ''} have multiple definitions: {','.join(map(lambda x: x, redefined_names))}"
        )
        self.redefined_names = redefined_names


def compile(files: t.Iterable[Path]) -> t.Container[CompiledFile]:
    obj_files = map(
        compile_source, map(lambda x: SourceFile(content=open(x).read(), path=x), files)
    )

    all_definitions = [
        definition
        for sublist in map(lambda x: x.definitions, obj_files)
        for definition in sublist
    ]
    if multiple_defined := set(
        map(
            lambda x: x[0],
            filter(
                lambda x: x[1] != 1,
                Counter(map(lambda x: x.name, all_definitions)).items(),
            ),
        )
    ):
        raise CrossFileRedefinitionError(multiple_defined)

    namespace: dict[str, float] = resolve_definitions(all_definitions)

    return list(
        map(
            lambda x: CompiledFile(content=compile_obj(x, namespace), path=x.path),
            obj_files,
        )
    )


def compile_obj(obj_file: ObjFile, namespace: dict[str, float]) -> str:
    return replace_spans_in_str(
        obj_file.content,
        itertools.chain(
            map(
                lambda x: (x.span, "{value:.2f}".format(value=namespace[x.name])),
                obj_file.definitions,
            ),
            map(
                lambda x: (x.span, "{name}".format(name=x.name.replace("_", " "))),
                obj_file.resolved_references,
            ),
        ),
    )


def replace_spans_in_str(
    source: str, replacements: t.Iterable[tuple[tuple[int, int], str]]
) -> str:
    replacements = (
        [((0, 0), "")]
        + sorted(replacements, key=lambda x: x[0][0])
        + [((len(source), len(source)), "")]
    )
    return "".join(
        map(
            lambda x: source[x[0][0][1] : x[1][0][0]] + x[1][1],
            zip(replacements[:-1], replacements[1:]),
        )
    )
