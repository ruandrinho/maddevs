"""
Tests for msg_split module
"""

import pytest

from msg_split import split_message


def test_split_message_default():
    """Tests split_message with default max_len"""
    with open("source.html", encoding="utf-8") as file:
        source = file.read()
    result = list(split_message(source))
    assert len(result) == 2
    assert len(result[0]) == 4085
    assert len(result[1]) == 1644


def test_split_message_exception():
    """Tests split_message with low max_len"""
    with open("source.html", encoding="utf-8") as file:
        source = file.read()
    with pytest.raises(ValueError):
        list(split_message(source, 10))
