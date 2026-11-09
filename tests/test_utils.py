"""
Test utility functions.
"""
import sys
import os
from datetime import date, time, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_parse_date():
    from bot.utils import parse_date

    # Standard format
    assert parse_date("2026-11-15") == date(2026, 11, 15)
    assert parse_date("2026/11/15") == date(2026, 11, 15)

    # European format
    assert parse_date("15-11-2026") == date(2026, 11, 15)

    # Invalid
    assert parse_date("not-a-date") is None
    assert parse_date("2026-13-01") is None  # month 13
    assert parse_date("") is None


def test_parse_time():
    from bot.utils import parse_time

    assert parse_time("14:00") == time(14, 0)
    assert parse_time("08:30") == time(8, 30)
    assert parse_time("23:59") == time(23, 59)
    assert parse_time("0") == time(0, 0)

    # Invalid
    assert parse_time("not-a-time") is None
    assert parse_time("25:00") is None
    assert parse_time("") is None


def test_to_timestamp():
    from bot.utils import to_timestamp

    d = date(2026, 11, 15)
    t = time(14, 0)
    ts = to_timestamp(d, t, "UTC")
    assert isinstance(ts, float)
    assert ts > 0


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


def test_truncate_text():
    from bot.utils import truncate_text

    assert truncate_text("Hello", 10) == "Hello"
    assert truncate_text("Hello World, this is a long text", 15) == "Hello World,..."
    assert truncate_text("", 10) == "(بدون متن)"
    assert truncate_text(None, 10) == "(بدون متن)"


def test_fmt_date():
    from bot.utils import fmt_date

    assert fmt_date(date(2026, 11, 15)) == "2026-11-15"
    assert fmt_date(date(2026, 1, 5)) == "2026-01-05"


def test_fmt_time():
    from bot.utils import fmt_time

    assert fmt_time(time(14, 0)) == "14:00"
    assert fmt_time(time(8, 5)) == "08:05"


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
