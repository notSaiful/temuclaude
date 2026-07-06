"""
Temuclaude Time and Timezone Module
Timezone conversion and current time queries.

Uses Python's zoneinfo (3.9+) for IANA timezone support.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import re
from typing import Optional, Dict, List


# Common IANA timezones
COMMON_TIMEZONES = {
    "UTC": "UTC",
    "GMT": "Etc/GMT",
    "EST": "America/New_York",
    "PST": "America/Los_Angeles",
    "CST": "America/Chicago",
    "MST": "America/Denver",
    "IST": "Asia/Kolkata",
    "BST": "Europe/London",
    "CET": "Europe/Paris",
    "EET": "Europe/Athens",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "HKT": "Asia/Hong_Kong",
    "SGT": "Asia/Singapore",
    "AEST": "Australia/Sydney",
    "AWST": "Australia/Perth",
    "GST": "Asia/Dubai",
    "AST": "Asia/Riyadh",
    "PKT": "Asia/Karachi",
    "BRT": "America/Sao_Paulo",
    "MSK": "Europe/Moscow",
    "TRT": "Europe/Istanbul",
}


def get_current_time(timezone_str: str = "UTC") -> Dict:
    """Get current time in a specific timezone.

    Args:
        timezone_str: IANA timezone name or abbreviation

    Returns:
        Dict with: timezone, datetime, date, time, day, iso
    """
    tz = _resolve_timezone(timezone_str)
    now = datetime.now(tz)

    return {
        "timezone": timezone_str,
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
        "iso": now.isoformat(),
    }


def convert_time(
    source_tz: str,
    time_str: str,
    target_tz: str,
) -> Dict:
    """Convert time between timezones.

    Args:
        source_tz: Source IANA timezone
        time_str: Time in HH:MM format (24-hour)
        target_tz: Target IANA timezone

    Returns:
        Dict with: source, target, source_time, target_time
    """
    src_tz = _resolve_timezone(source_tz)
    tgt_tz = _resolve_timezone(target_tz)

    # Parse time string
    hour, minute = map(int, time_str.split(":"))

    # Create datetime with today's date in source timezone
    today = datetime.now(src_tz).date()
    src_dt = datetime(today.year, today.month, today.day, hour, minute, tzinfo=src_tz)

    # Convert to target timezone
    tgt_dt = src_dt.astimezone(tgt_tz)

    return {
        "source": source_tz,
        "target": target_tz,
        "source_time": src_dt.strftime("%H:%M %Z"),
        "target_time": tgt_dt.strftime("%H:%M %Z"),
        "source_iso": src_dt.isoformat(),
        "target_iso": tgt_dt.isoformat(),
    }


def _resolve_timezone(tz_str: str) -> ZoneInfo:
    """Resolve a timezone string to ZoneInfo.

    Handles:
    - IANA names (America/New_York)
    - Abbreviations (EST, PST)
    - UTC/GMT
    """
    if tz_str.upper() in ("UTC", "GMT"):
        return timezone.utc

    # Check abbreviation map
    if tz_str.upper() in COMMON_TIMEZONES:
        return ZoneInfo(COMMON_TIMEZONES[tz_str.upper()])

    # Try as IANA name
    try:
        return ZoneInfo(tz_str)
    except Exception:
        raise ValueError(f"Unknown timezone: {tz_str}")


def list_timezones() -> List[str]:
    """List common IANA timezones."""
    return sorted(COMMON_TIMEZONES.keys())


def detect_timezone_in_query(text: str) -> List[str]:
    """Extract timezone references from text.

    Returns list of timezone strings found.
    """
    found = []
    text_lower = text.lower()

    # Check abbreviations
    for abbr in COMMON_TIMEZONES:
        if re.search(r'\b' + abbr.lower() + r'\b', text_lower):
            found.append(abbr)

    # Check IANA patterns (Continent/City)
    iana_match = re.findall(
        r'\b(Africa|America|Asia|Europe|Australia|Pacific|Antarctica|Atlantic|Indian|Arctic)/[\w_/]+',
        text
    )
    if iana_match:
        found.extend(iana_match)

    # Check UTC/GMT
    if re.search(r'\b(utc|gmt)\b', text_lower):
        if "UTC" not in found:
            found.append("UTC")

    return list(set(found))


def detect_time_in_query(text: str) -> Optional[str]:
    """Detect a time reference in text (HH:MM format)."""
    match = re.search(r'\b(\d{1,2}):(\d{2})\b', text)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"
    return None


def is_time_query(text: str) -> bool:
    """Check if the text is asking about time or timezones."""
    time_keywords = [
        "what time", "current time", "time in", "timezone",
        "convert time", "what is the time", "local time",
        "time now", "time difference", "hours ahead", "hours behind",
    ]
    text_lower = text.lower()

    for kw in time_keywords:
        if kw in text_lower:
            return True

    # Check for timezone abbreviations
    if detect_timezone_in_query(text):
        return True

    return False