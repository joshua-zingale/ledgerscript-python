import sys
from .compilation import compile

    

def ledgerscript_cli():
    print(compile(sys.stdin.read()))
