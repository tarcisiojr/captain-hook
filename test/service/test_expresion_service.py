import pytest

from app.service import expression_service


@pytest.mark.parametrize("expression, variables, expected", [
    ("10 > 20", {}, False),
    ("12.3 + 30 > 40", {}, True),
    ("12 > 40 - 30", {}, True),
    ("a == 40", {"a": 40}, True),
    ("a >= b.c", {"a": 40, "b": {"c": 90}}, False),
    ("a < b.c", {"a": 40, "b": {"c": 90}}, True),
    ("b.c", {"a": 40, "b": {"c": 90}}, 90),
    ("b.c < 10 or true", {"a": 40, "b": {"c": 90}}, True),
    ("b.c < 10 or 1 == 2", {"a": 40, "b": {"c": 90}}, False),
    ("b.c < 100 and TruE", {"a": 40, "b": {"c": 90}}, True),
    ("b.c > 100 and TruE", {"a": 40, "b": {"c": 90}}, False),
    ("b.c * -1", {"a": 40, "b": {"c": 90}}, -90),
    ("b.c**3", {"b": {"c": 2}}, 8),
])
def test_evaluate(expression, variables, expected):
    assert expression_service.evaluate(expression, variables) == expected