import pytest
from app.agents.task_decomposer.decomposer import enterprise_task_decomposer


def test_tc_gmail_delete_01_delete_the_email():
    res = enterprise_task_decomposer.decompose("Delete the email")
    assert len(res.tasks) == 3
    assert res.tasks[0].provider == "gmail"
    assert res.tasks[2].operation == "gmail.messages.delete"


def test_tc_gmail_delete_02_delete_the_message():
    res = enterprise_task_decomposer.decompose("Delete the message")
    assert len(res.tasks) == 3
    assert res.tasks[0].provider == "gmail"
    assert res.tasks[2].operation == "gmail.messages.delete"


def test_tc_gmail_delete_03_delete_gmail_messages():
    res = enterprise_task_decomposer.decompose("Delete Gmail messages")
    assert len(res.tasks) == 3
    assert res.tasks[0].provider == "gmail"
    assert res.tasks[2].operation == "gmail.messages.delete"


def test_tc_gmail_delete_04_trash_this_email():
    res = enterprise_task_decomposer.decompose("Trash this email")
    assert len(res.tasks) == 3
    assert res.tasks[0].provider == "gmail"
    assert res.tasks[2].operation == "gmail.messages.delete"


def test_tc_gmail_delete_05_delete_a_pet():
    res = enterprise_task_decomposer.decompose("Delete a pet")
    has_gmail_delete = any(t.provider == "gmail" and t.operation == "gmail.messages.delete" for t in res.tasks)
    assert not has_gmail_delete, "Delete a pet was incorrectly classified as Gmail delete"


def test_tc_gmail_delete_06_delete_a_user():
    res = enterprise_task_decomposer.decompose("Delete a user")
    has_gmail_delete = any(t.provider == "gmail" and t.operation == "gmail.messages.delete" for t in res.tasks)
    assert not has_gmail_delete, "Delete a user was incorrectly classified as Gmail delete"


def test_tc_gmail_delete_07_delete_an_order():
    res = enterprise_task_decomposer.decompose("Delete an order")
    has_gmail_delete = any(t.provider == "gmail" and t.operation == "gmail.messages.delete" for t in res.tasks)
    assert not has_gmail_delete, "Delete an order was incorrectly classified as Gmail delete"


def test_tc_gmail_delete_08_delete_resource_with_openapi_spec():
    prompt = "Delete a resource using this OpenAPI specification: https://petstore3.swagger.io/api/v3/openapi.json"
    res = enterprise_task_decomposer.decompose(prompt)
    has_gmail_delete = any(t.provider == "gmail" and t.operation == "gmail.messages.delete" for t in res.tasks)
    assert not has_gmail_delete, "Delete with OpenAPI spec was incorrectly classified as Gmail delete"


def test_tc_gmail_delete_09_negative_intent_no_gmail_delete():
    res = enterprise_task_decomposer.decompose("Do not delete the email")
    has_gmail_delete = any(t.provider == "gmail" and t.operation == "gmail.messages.delete" for t in res.tasks)
    assert not has_gmail_delete, "Negative delete intent created a Gmail deletion task"
