import re
from collections.abc import Callable, Sequence
from typing import Optional, TypeVar

import funcparserlib.lexer as funclex
from funcparserlib.parser import NoParseError, finished, forward_decl, many, maybe, tok

from . import GlobExpr, Literal, _GlobGroup

SPECIAL_CHARS: tuple[str, ...] = Literal._SPECIAL_CHARS


def _special_char_pattern(*, invert: bool = False, repeat: str = "") -> str:
    res = ["["]
    if invert:
        res.append("^")
    for c in SPECIAL_CHARS:
        res.append(re.escape(c))
    res.append("]")
    if repeat:
        res.append(repeat)
    return "".join(res)


TOKENIZER = funclex.make_tokenizer(
    [
        funclex.TokenSpec("op", _special_char_pattern()),
        funclex.TokenSpec("word", _special_char_pattern(invert=True, repeat="+")),
    ]
)


def _process_literal(text: Optional[list[str]]) -> Literal:
    return Literal("".join(text)) if text is not None else Literal.EMPTY


def _process_group(
    parts: tuple[Literal, tuple[GlobExpr, Sequence[GlobExpr]], GlobExpr]
) -> _GlobGroup:
    prefix, (first_child, children), suffix = parts
    return _GlobGroup(prefix, [first_child, *children], suffix)


T = TypeVar("T")


def _or_default(default: T, /) -> Callable[[Optional[T]], T]:
    return lambda item: item if item is not None else default


_expr = forward_decl()
_maybe_expr = maybe(_expr) >> _or_default(Literal.EMPTY)
_word = tok("word")
_escape_seq = -tok("op", "\\") + tok("op")
_nonempty_literal = many(_escape_seq | _word) >> _process_literal
_literal = maybe(_nonempty_literal) >> _or_default(Literal.EMPTY)

_group = (
    _literal
    + (  # prefix
        -tok("op", "{")
        + (_maybe_expr + many(-tok("op", ",") + _maybe_expr))
        + -tok("op", "}")
    )
    + _maybe_expr
) >> _process_group
_expr.define(_group | _nonempty_literal)

whole_literal = _literal + -finished
whole_expr = _expr + -finished
