import sys
from .compilation import compile_str


def main():
    cli(sys.argv)


def cli(argv: list[str]):
    sys.stdout.write(compile_str(sys.stdin.read()))
