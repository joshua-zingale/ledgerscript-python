import enum
import typing as t
import operator as op
from dataclasses import dataclass
import re


class TokenKind(enum.Enum):
    PLUS = 0
    MINUS = 1
    MUL = 2
    DIV = 3

    NAME = 4
    NUM = 5

    LPAREN = 6
    RPAREN = 7


ArithmeticOperators: t.TypeAlias = (
    t.Literal[TokenKind.PLUS]
    | t.Literal[TokenKind.MINUS]
    | t.Literal[TokenKind.MUL]
    | t.Literal[TokenKind.DIV]
)


@dataclass
class Token[T]:
    kind: T
    lexeme: str


class InvalidExpressionError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Invalid Expression")


op_precedence: dict[ArithmeticOperators, int] = {
    TokenKind.PLUS: 10,
    TokenKind.MINUS: 10,
    TokenKind.MUL: 20,
    TokenKind.DIV: 20,
}


class InvalidTokenError(RuntimeError):
    def __init__(self, pos: int) -> None:
        super().__init__(f"Invalid token at character {pos}")
        self.pos = pos


def make_tokenizer[T](
    rules: dict[str, T], regex_prefix: str = r"\s*(", regex_postfix: str = r")\s*"
) -> t.Callable[[str], list[Token[T]]]:
    compiled_rules = list(
        map(
            lambda x: (re.compile(f"{regex_prefix}{x[0]}{regex_postfix}"), x[1]),
            rules.items(),
        )
    )

    def tokenize(source: str) -> list[Token[T]]:
        source_len = len(source)
        tokens: list[Token[T]] = []

        while match_and_kind := next(
            filter(
                lambda x: x[0] is not None,
                map(lambda x: (x[0].match(source), x[1]), compiled_rules),
            ),
            None,
        ):
            lexeme_match, kind = match_and_kind
            assert lexeme_match
            source = source[lexeme_match.end() :]
            tokens.append(Token(kind, lexeme_match.groups()[0]))

        if source:
            raise InvalidTokenError(source_len - len(source))
        return tokens

    return tokenize


_tokenize_expression = make_tokenizer(
    {
        r"[a-zA-Z][\w_]+": TokenKind.NAME,
        r"(?:\d*\.)?\d+": TokenKind.NUM,
        r"\+": TokenKind.PLUS,
        r"-": TokenKind.MINUS,
        r"\*": TokenKind.MUL,
        r"/": TokenKind.DIV,
        r"\(": TokenKind.LPAREN,
        r"\)": TokenKind.RPAREN,
    }
)


def tokenize_expression(source: str) -> list[Token[TokenKind]]:
    return _tokenize_expression(source)


class ParsingError(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def parse_expression(source: str) -> "Production":
    tokens = tokenize_expression(source)
    op_stack: list[ArithmeticOperators | t.Literal[TokenKind.LPAREN]] = []
    productions: list[Production] = []

    for token in tokens:
        match token.kind:
            case TokenKind.NUM:
                productions.append(float(token.lexeme))
            case TokenKind.NAME:
                productions.append(token.lexeme)
            case TokenKind.LPAREN:
                op_stack.append(TokenKind.LPAREN)
            case TokenKind.RPAREN:
                operator = None
                while op_stack and (operator := op_stack.pop()) != TokenKind.LPAREN:
                    productions.append(produce(operator, productions))
                if not operator:
                    raise ParsingError("Unmatched right parenthesis")
            case TokenKind.PLUS | TokenKind.MINUS | TokenKind.MUL | TokenKind.DIV:
                while (
                    op_stack
                    and (tos := op_stack[-1])
                    and tos != TokenKind.LPAREN
                    and op_precedence[token.kind] < op_precedence[tos]
                ):
                    op_stack.pop()
                    productions.append(produce(tos, productions))
                op_stack.append(token.kind)

    while op_stack:
        tos = op_stack.pop()
        if tos == TokenKind.LPAREN:
            raise ParsingError("Unmatched left parenthesis")
        productions.append(produce(tos, productions))

    if len(productions) != 1:
        print(productions)
        raise ParsingError("Invalid expression")

    return productions[0]


def produce(operator: ArithmeticOperators, production_stack: list["Production"]):
    match operator:
        case TokenKind.PLUS:
            return BinOp(
                op.add, right=production_stack.pop(), left=production_stack.pop()
            )
        case TokenKind.MINUS:
            return BinOp(
                op.sub, right=production_stack.pop(), left=production_stack.pop()
            )
        case TokenKind.MUL:
            return BinOp(
                op.mul, right=production_stack.pop(), left=production_stack.pop()
            )
        case TokenKind.DIV:
            return BinOp(
                op.truediv, right=production_stack.pop(), left=production_stack.pop()
            )


Production: t.TypeAlias = t.Union["BinOp", "UnaryOp", str, float]


@dataclass
class UnaryOp:
    op: t.Callable[[float], float]
    arg: Production


@dataclass
class BinOp:
    op: t.Callable[[float, float], float]
    left: Production
    right: Production
