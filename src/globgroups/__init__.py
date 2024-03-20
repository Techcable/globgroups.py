"""
Expands globs with grouping like foo{bar,baz}
"""

from __future__ import annotations

import functools
import itertools
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import ClassVar, ForwardRef, Optional

from funcparserlib.lexer import LexerError, Token
from funcparserlib.parser import NoParseError, Parser
from typing_extensions import Self, TypeAlias, final, override

from ._version import __version__

__all__ = ("GlobExpr", "Literal")

_TokenizerType: TypeAlias = Callable[[str], Iterable[Token]]


class GlobExpr(metaclass=ABCMeta):
    _PARSER: ClassVar[Optional[Parser[Token, GlobExpr]]] = None
    _TOKENIZER: ClassVar[Optional[_TokenizerType]] = None

    def expand(self) -> list[str]:
        """Expand the glob expression"""
        return list(self._expand_iter())

    @abstractmethod
    def equivalent_expr(self) -> str:
        """
        Create an expression which is semantically equivalent to this glob

        Not necessarily exactly equal to the original expression.
        """

    @abstractmethod
    def _expand_iter(self) -> Iterator[str]:
        """An iterator over the expansion of self"""

    @classmethod
    def _init_parser(cls) -> Parser[Token, GlobExpr]:
        from ._parse import whole_expr

        return whole_expr

    @classmethod
    def parse(cls, text: str) -> GlobExpr:
        if not text:
            return Literal.EMPTY
        if (parser := cls._PARSER) is None:
            parser = cls._PARSER = cls._init_parser()
        if (tokenizer := GlobExpr._TOKENIZER) is None:
            from . import _parse

            tokenizer = GlobExpr._TOKENIZER = _parse.TOKENIZER
        try:
            return parser.parse(list(tokenizer(text)))
        except (LexerError, NoParseError):
            raise GlobParseError(f"Failed to parse {cls.__name__}: {text!r}")

    def __repr__(self) -> str:
        return f"GlobExpr.parse({self.equivalent_expr()!r})"


@dataclass(frozen=True)
class Literal(GlobExpr):
    """A literal glob expression, that expands to its textual value"""

    text: str

    _SPECIAL_CHARS: ClassVar[tuple[str, ...]] = ("{", "}", ",", "\\")
    EMPTY: ClassVar[Literal]

    @override
    def expand(self) -> list[str]:
        return [self.text]

    @override
    def equivalent_expr(self) -> str:
        res = []
        for c in self.text:
            if c in Literal._SPECIAL_CHARS:
                res.append("\\")
            res.append(c)
        return "".join(res)

    @staticmethod
    def escape(text: str) -> str:
        """
        Escape any special characters in the text

        The result can be successfully parsed as a glob Literal.
        """
        return Literal(text).equivalent_expr()

    @override
    @classmethod
    def parse(cls, text: str) -> Literal:
        res = super().parse(text)
        assert isinstance(res, Literal)
        return res

    @override
    def _expand_iter(self) -> Iterator[str]:
        yield self.text

    @override
    @classmethod
    def _init_parser(cls) -> Parser[Token, GlobExpr]:
        from ._parse import whole_literal

        return whole_literal

    @staticmethod
    def _process_parse(txt: Optional[list[str]]) -> Literal:
        return Literal("".join(txt)) if txt is not None else Literal.EMPTY

    @override
    def __repr__(self) -> str:
        return f"Literal({self.text!r})"


Literal.EMPTY = Literal("")


class GlobParseError(ValueError):
    """An error that occurs parsing a GlobExpr"""


@dataclass
class _GlobGroup(GlobExpr):
    """
    A glob group prefix{child1,child2}suffix

    This type is an implementation detail.
    """

    _prefix: Literal
    _children: list[GlobExpr]
    _suffix: GlobExpr

    def __post_init__(self):
        assert isinstance(self._prefix, Literal), "Prefix must be literal"
        assert self._children, "Empty children"

    @override
    def _expand_iter(self) -> Iterator[str]:
        suffixes: list[str] = self._suffix.expand()
        for child in self._children:
            for child_expansion in child._expand_iter():
                for suffix_expansion in suffixes:
                    yield self._prefix.text + child_expansion + suffix_expansion

    @override
    def equivalent_expr(self) -> str:
        parts = [self._prefix.equivalent_expr()]
        if self._children:
            parts.append("{")
            parts.extend(",".join(child.equivalent_expr() for child in self._children))
            parts.append("}")
        parts.append(self._suffix.equivalent_expr())
        return "".join(parts)
