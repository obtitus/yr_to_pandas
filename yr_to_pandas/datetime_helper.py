# Standard library imports
import datetime

# third party imports
import pytz


def convert_utc_to_local(time):
    """Convert UTC timestamp to local time without tzinfo"""
    # Probably a easier solution to this
    time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    time = time.replace(tzinfo=pytz.UTC)
    time = time.astimezone()
    time = time.replace(tzinfo=None)

    return time
