from io import StringIO
import contextlib
from ledgerscript.cli import cli

def test_plain_text_is_unchainged_through_stdio():
    standard_input = """Amazing grace! How sweet the sound
    That saved a wretch like me:
    I once was lost but now am found;
    was blind but now I see."""

    assert _cli(standard_input) == standard_input


def test_single_constant_with_reference():
    standard_input = """I have $@=Bank_Account[500] in my @<."""
    out = _cli(standard_input)

    assert appear_in_order(out, "500", "Bank Account")

def test_two_constants_with_references():
    standard_input = """In my @>, I have $@=Bank_Account[500], but Tom has $@=His_Account[800] in his in @<."""
    out = _cli(standard_input)
    assert appear_in_order(out, "Bank Account", "500", "800", "His Account")

def test_intra_definition_arithmetic():
    standard_input = """@=b[(3 * (1 + 3) - 2) / 2 + 3]"""
    assert _cli(standard_input).startswith("8")

def test_operator_precedence():
    standard_input = "@=b[4 - 3 + 2 * 10]."
    assert _cli(standard_input).startswith("21")

def test_arithmetic_with_variables():
    standard_input = """I make $@=yearly_salary[4*dollars_per_quarter] a year because I make @=dollars_per_quarter[10000] @<"""
    assert appear_in_order(_cli(standard_input), "I", "40", "000", "10000", "dollars per quarter")


def appear_in_order(string: str, *substrings: str) -> bool:
    indices = list(map(string.find, substrings))
    if min(indices) == -1:
        return False
    return sorted(indices) == indices

def _cli(input: str) -> str:
    standard_output = StringIO()
    with contextlib.redirect_stdout(standard_output):
        cli(["test"], StringIO(input))
    standard_output.seek(0)
    return standard_output.read()
