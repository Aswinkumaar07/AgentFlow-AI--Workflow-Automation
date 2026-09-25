import pytest
from app.agents.expressions import (
    expression_generator,
    expression_validator,
    expression_ai_service,
    ExpressionResult,
)


def test_expression_generator_uppercase():
    res = expression_ai_service.generate("Convert to uppercase")
    assert isinstance(res, ExpressionResult)
    assert res.expression == "{{$node.Gmail.subject.toUpperCase()}}"
    assert res.category == "String"
    assert res.is_valid is True


def test_expression_generator_today_and_uuid():
    res_today = expression_ai_service.generate("Today's date")
    assert res_today.expression == "{{$today}}"
    assert res_today.category == "Date"
    assert res_today.is_valid is True

    res_uuid = expression_ai_service.generate("UUID")
    assert res_uuid.expression == "{{$uuid}}"
    assert res_uuid.category == "System"
    assert res_uuid.is_valid is True


def test_expression_generator_math_and_array():
    res_math = expression_ai_service.generate("round", target_var="$node.Sheets.amount")
    assert res_math.expression == "{{Math.round($node.Sheets.amount)}}"
    assert res_math.category == "Math"

    res_arr = expression_ai_service.generate("array length", target_var="$node.Sheets.values")
    assert res_arr.expression == "{{$node.Sheets.values.length}}"
    assert res_arr.category == "Array"


def test_expression_validator_valid():
    is_valid, err = expression_validator.validate_expression("{{$node.Gmail.subject.toUpperCase()}}")
    assert is_valid is True
    assert err is None


def test_expression_validator_mismatched_braces():
    is_valid, err = expression_validator.validate_expression("{{$node.Gmail.subject.toUpperCase()")
    assert is_valid is False
    assert "Mismatched expression braces" in err


def test_expression_validator_unbalanced_parens():
    is_valid, err = expression_validator.validate_expression("{{$node.Gmail.subject.toUpperCase(}}")
    assert is_valid is False
    assert "Unbalanced parentheses" in err
