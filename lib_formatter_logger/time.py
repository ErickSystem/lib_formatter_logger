"""This module is responsable to convert to/from datetime to/from UNIX Timestamp in nanosseconds
"""

from datetime import datetime, timezone


def from_ns_timestamp(timestamp, timezone=timezone.utc):
    """Converts nanoseconds timestamp to datetime

    Arguments:
        timestamp {int} -- The timestamp to convert to datetime
        timezone {obj} -- A datetime.timezone object (default: {timezone.utc})

    Returns:
        [datetime.datetime] -- the converted timestamp
    """
    timestamp = timestamp / 10 ** 9
    return datetime.fromtimestamp(timestamp, timezone)


def to_ns_timestamp(date_time):
    """Converts a datetime object to timestamp in nanoseconds
    assume utc if a naive datetime

    Arguments:
        date_time {obj} -- a datetime.datetime object

    Returns:
        [int] -- The converted datetime.datetime object into nanosecond timestamp
    """
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=timezone.utc)

    return int(date_time.timestamp() * 10 ** 6) * 10 ** 3
