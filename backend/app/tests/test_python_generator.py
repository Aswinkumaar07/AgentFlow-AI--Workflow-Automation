import pytest
from app.agents.code_generator import (
    python_code_generator,
    code_validator,
    code_generator_ai_service,
    CodeGenerationResult,
)


def test_code_generator_csv_processing():
    res = code_generator_ai_service.generate_python_node("Process CSV file")
    assert isinstance(res, CodeGenerationResult)
    assert res.task_type == "CSV Processing"
    assert "def main(input_data):" in res.code
    assert "import csv" in res.code
    assert res.is_valid is True
    assert res.syntax_error is None


def test_code_generator_json_and_regex():
    res_json = code_generator_ai_service.generate_python_node("Transform JSON payload")
    assert res_json.task_type == "JSON Transformation"
    assert res_json.is_valid is True

    res_regex = code_generator_ai_service.generate_python_node("Regex extract email addresses")
    assert res_regex.task_type == "Regex Pattern Extraction"
    assert res_regex.is_valid is True


def test_code_generator_pandas_analysis():
    res = code_generator_ai_service.generate_python_node("Analyze dataframe with pandas")
    assert res.task_type == "Pandas Dataframe Analysis"
    assert "import pandas as pd" in res.code
    assert res.is_valid is True


def test_code_validator_valid_ast():
    code = "def main(x):\n    return x * 2\n"
    is_valid, err = code_validator.validate_python_code(code)
    assert is_valid is True
    assert err is None


def test_code_validator_invalid_ast():
    invalid_code = "def main(:\n    return 42"
    is_valid, err = code_validator.validate_python_code(invalid_code)
    assert is_valid is False
    assert err is not None
    assert "SyntaxError" in err
