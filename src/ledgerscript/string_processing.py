import typing as t

def replace_spans_in_str(source: str, replacements: t.Iterable[tuple[tuple[int,int], str]]) -> str:
    replacements = [((0,0), "")] + sorted(replacements, key=lambda x: x[0][0]) + [((len(source), len(source)), "")]
    return "".join(map(lambda x: source[x[0][0][1]:x[1][0][0]] + x[1][1], zip(replacements[:-1], replacements[1:])))