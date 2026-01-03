import sys
from .compilation import compile


def ledgerscript_cli():
    sys.stdout.write(compile(sys.stdin.read()))
