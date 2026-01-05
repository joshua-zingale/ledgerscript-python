"""Compiles a text with ledgerscript, \
    producing a new text with the ledgerscript expressions replaced by numbers and reference names.

If no files are specified, the input and output are standard IO.
Otherwise, the input files are all received, compiled together,
allowing references to be shared among them, and the compiled files
are output into the target directory.
"""
import sys
import os
from pathlib import Path
from argparse import ArgumentParser

from .compilation import compile_str, compile, SourceFile


def main():
    cli(sys.argv)


def cli(argv: list[str]):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('files', metavar='FILE', nargs='+', help='Input file(s) to process. If none is specified, standard input is used.')
    parser.add_argument('--target', "-t", default="./target", help='The output directory for the compiled files if input files are specified. If no input files are specified, specifying this as an argument has no effect.')

    args = parser.parse_args(argv)
    files: list[Path] = list(map(lambda x: Path(x), args.files[1:]))
    output_dir = Path(args.target)
    if files:
        for compiled_file in compile(map(lambda x: SourceFile(content=open(x).read(), path=x), files)):
            filepath = output_dir / compiled_file.path
            os.makedirs(filepath.parent, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(compiled_file.content)
    else:
        sys.stdout.write(compile_str(sys.stdin.read()))


if __name__ == "__main__":
    main()