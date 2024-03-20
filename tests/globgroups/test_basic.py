from dataclasses import dataclass

import pytest

from globgroups import GlobExpr


@dataclass
class GlobTest:
    expression: str
    expected_expansions: list[str]


TEST_DATA: list[GlobTest] = [
    GlobTest("foo-{bar,baz}-beat", ["foo-bar-beat", "foo-baz-beat"]),
    GlobTest(
        "foo-{bar,beat{nest,foop}}-baz",
        ["foo-bar-baz", "foo-beatnest-baz", "foo-beatfoop-baz"],
    ),
    GlobTest(
        "foo{,-\\{baz{teach,wo\\,\\}}}\\\\\\{",
        ["foo\\{", "foo-{bazteach\\{", "foo-{bazwo,}\\{"],
    ),
    GlobTest("feet\\{\\\\\\}", ["feet{\\}"]),
]


@pytest.mark.parametrize(
    "expression,expected_expansions",
    [(test.expression, test.expected_expansions) for test in TEST_DATA],
)
def test_expansions(expression: str, expected_expansions: str):
    glob = GlobExpr.parse(expression)
    assert glob.expand() == expected_expansions


@pytest.mark.parametrize(
    "expression",
    [test.expression for test in TEST_DATA],
)
def test_roundtrip(expression: str):
    glob = GlobExpr.parse(expression)
    assert glob.equivalent_expr() == expression
