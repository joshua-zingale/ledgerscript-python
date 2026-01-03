import itertools
import typing as t

from .definition import get_definitions, get_references, resolve_definitions, resolve_references

def compile(source: str) -> str:

    definitions = get_definitions(source)
    references = get_references(source)
    resolved_references = resolve_references(references, definitions)
    namespace = resolve_definitions(definitions)

    return replace_spans_in_str(
        source,
        itertools.chain(
            map(lambda x: (x.span, f"{namespace[x.name]:.2f}"), definitions),
            map(lambda x: (x.span, x.name.replace("_", " ")), resolved_references)
        )
        )
    

def replace_spans_in_str(source: str, replacements: t.Iterable[tuple[tuple[int,int], str]]) -> str:
    replacements = [((0,0), "")] + sorted(replacements, key=lambda x: x[0][0]) + [((len(source), len(source)), "")]
    return "".join(map(lambda x: source[x[0][0][1]:x[1][0][0]] + x[1][1], zip(replacements[:-1], replacements[1:])))
