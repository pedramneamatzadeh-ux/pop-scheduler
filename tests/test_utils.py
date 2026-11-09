"""
Test utility functions.
"""
import sys
import os
from datetime import date, time, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_normalize_digits():
    from bot.utils import normalize_digits
    
    assert normalize_digits("۱۲۳") == "123"
    assert normalize_digits("٤٥٦") == "456"
    assert normalize_digits("abc") == "abc"
    assert normalize_digits(None) == ""


def test_parse_message_ids():
    from bot.utils import parse_message_ids
    
    # Single ID
    assert parse_message_ids("10") == [10]
    
    # Range
    assert parse_message_ids("10-15") == [10, 11, 12, 13, 14, 15]
    
    # Multiple
    assert parse_message_ids("10,13,17") == [10, 13, 17]
    
    # Combined
    assert parse_message_ids("10,13-15,17") == [10, 13, 14, 15, 17]
    
    # With Persian comma
    assert parse_message_ids("10،13،17") == [10, 13, 17]
    
    # With spaces
    assert parse_message_ids("10, 13, 17") == [10, 13, 17]
    
    # Invalid
    assert parse_message_ids("abc") is None
    assert parse_message_ids("") is None
    assert parse_message_ids("-5") is None
    assert parse_message_ids("15-10") is None
    
    # Duplicates removed
    assert parse_message_ids("10,10,10") == [10]


def test_validate_hour_input():
    from bot.utils import validate_hour_input
    
    # Valid formats
    assert validate_hour_input("14") == (True, 14, 0)
    assert validate_hour_input("14:30") == (True, 14, 30)
    assert validate_hour_input("08:05") == (True, 8, 5)
    assert validate_hour_input("0") == (True, 0, 0)
    assert validate_hour_input("23:59") == (True, 23, 59)
    
    # Invalid formats
    assert validate_hour_input("25")[0] is False
    assert validate_hour_input("14:60")[0] is False
    assert validate_hour_input("abc")[0] is False
    assert validate_hour_input("")[0] is False


def test_get_month_days():
    from bot.utils import get_month_days
    
    # January has 31 days
    assert get_month_days(2024, 1) == 31
    
    # February in leap year
    assert get_month_days(2024, 2) == 29
    
    # February in non-leap year
    assert get_month_days(2023, 2) == 28
    
    # April has 30 days
    assert get_month_days(2024, 4) == 30


def test_paginate():
    from bot.utils import paginate
    
    items = list(range(20))
    
    # Page 0
    page, total = paginate(items, 0, 5)
    assert page == [0, 1, 2, 3, 4]
    assert total == 4
    
    # Page 1
    page, total = paginate(items, 1, 5)
    assert page == [5, 6, 7, 8, 9]
    assert total == 4
    
    # Last page
    page, total = paginate(items, 3, 5)
    assert page == [15, 16, 17, 18, 19]
    
    # Out of range → clamp
    page, total = paginate(items, 10, 5)
    assert page == [15, 16, 17, 18, 19]
    
    page, total = paginate(items, -5, 5)
    assert page == [0, 1, 2, 3, 4]


def test_to_timestamp():
    from bot.utils import to_timestamp
    
    ts = to_timestamp(2026, 11, 15, 14)
    assert isinstance(ts, float)
    assert ts > 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    sys.exit(1 if failed else 0)
