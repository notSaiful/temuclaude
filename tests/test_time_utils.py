"""Tests for time_utils module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.time_utils import (
    get_current_time, convert_time, list_timezones,
    detect_timezone_in_query, is_time_query
)


def test_get_current_time_utc():
    result = get_current_time("UTC")
    assert "UTC" in result["timezone"]
    assert "date" in result
    assert "time" in result
    assert "day" in result


def test_get_current_time_ist():
    result = get_current_time("IST")
    assert result["date"]  # should have a date
    assert len(result["time"]) > 0


def test_get_current_time_iana():
    result = get_current_time("America/New_York")
    assert result["date"]
    assert result["day"]


def test_convert_time():
    result = convert_time("UTC", "12:00", "IST")
    assert "source" in result
    assert "target" in result
    assert "12:00" in result["source_time"]


def test_convert_time_us():
    result = convert_time("EST", "09:00", "PST")
    assert "09:00" in result["source_time"]
    # 9am EST = 6am PST
    assert "06:00" in result["target_time"]


def test_list_timezones():
    tzs = list_timezones()
    assert "UTC" in tzs
    assert "IST" in tzs
    assert "EST" in tzs


def test_detect_timezone_in_query():
    result = detect_timezone_in_query("What time is it in EST?")
    assert "EST" in result


def test_detect_timezone_iana():
    result = detect_timezone_in_query("Convert from America/New_York to Asia/Tokyo")
    assert len(result) >= 1


def test_is_time_query_yes():
    assert is_time_query("What time is it in Tokyo?") == True
    assert is_time_query("Convert 9am EST to PST") == True


def test_is_time_query_no():
    assert is_time_query("What is Python?") == False
    assert is_time_query("How to cook rice?") == False