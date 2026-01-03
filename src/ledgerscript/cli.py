import sys

from .definition import get_definitions, resolve_definitions
def ledgerscript_cli():
    print(resolve_definitions(get_definitions(sys.stdin.read())))
