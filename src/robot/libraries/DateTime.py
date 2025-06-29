#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""A library for handling date and time values.

``DateTime`` is a Robot Framework standard library that supports creating and
converting date and time values (e.g. `Get Current Date`, `Convert Time`),
as well as doing simple calculations with them (e.g. `Subtract Time From Date`,
`Add Time To Time`). It supports dates and times in various formats, and can
also be used by other libraries programmatically.

== Table of contents ==

%TOC%

= Terminology =

In the context of this library, ``date`` and ``time`` generally have the following
meanings:

- ``date``: An entity with both date and time components but without any
   time zone information. For example, ``2014-06-11 10:07:42``.
- ``time``: A time interval. For example, ``1 hour 20 minutes`` or ``01:20:00``.

This terminology differs from what Python's standard
[http://docs.python.org/library/datetime.html|datetime] module uses.
Basically its
[http://docs.python.org/library/datetime.html#datetime-objects|datetime] and
[http://docs.python.org/library/datetime.html#timedelta-objects|timedelta]
objects match ``date`` and ``time`` as defined by this library.

= Date formats =

Dates can be given to and received from keywords in `timestamp`, `custom
timestamp`, `Python datetime` and `epoch time` formats. These formats are
discussed thoroughly in subsequent sections.

Input format is determined automatically based on the given date except when
using custom timestamps, in which case it needs to be given using
``date_format`` argument. Default result format is timestamp, but it can
be overridden using ``result_format`` argument.

== Timestamp ==

If a date is given as a string, it is always considered to be a timestamp.
If no custom formatting is given using ``date_format`` argument, the timestamp
is expected to be in [http://en.wikipedia.org/wiki/ISO_8601|ISO 8601] like
format ``YYYY-MM-DD hh:mm:ss.mil``, where any non-digit character can be used
as a separator or separators can be omitted altogether. Additionally,
only the date part is mandatory, all possibly missing time components are
considered to be zeros.

Dates can also be returned in the same ``YYYY-MM-DD hh:mm:ss.mil`` format by
using ``timestamp`` value with ``result_format`` argument. This is also the
default format that keywords returning dates use. Milliseconds can be excluded
using ``exclude_millis`` as explained in `Millisecond handling` section.

Examples:
| ${date1} =      | Convert Date | 2014-06-11 10:07:42.000 |
| ${date2} =      | Convert Date | 20140611 100742         | result_format=timestamp |
| Should Be Equal | ${date1}     | ${date2}                |
| ${date} =       | Convert Date | 20140612 12:57          | exclude_millis=yes |
| Should Be Equal | ${date}      | 2014-06-12 12:57:00     |

== Custom timestamp ==

It is possible to use custom timestamps in both input and output.
The custom format is same as accepted by Python's
[http://docs.python.org/library/datetime.html#strftime-strptime-behavior|
datetime.strptime] function. For example, the default timestamp discussed
in the previous section would match ``%Y-%m-%d %H:%M:%S.%f``.

When using a custom timestamp in input, it must be specified using
``date_format`` argument. The actual input value must be a string that matches
the specified format exactly. When using a custom timestamp in output, it must
be given using ``result_format`` argument.

Examples:
| ${date} =       | Convert Date | 28.05.2014 12:05        | date_format=%d.%m.%Y %H:%M |
| Should Be Equal | ${date}      | 2014-05-28 12:05:00.000 |
| ${date} =       | Convert Date | ${date}                 | result_format=%d.%m.%Y |
| Should Be Equal | ${date}      | 28.05.2014              |

== Python datetime ==

Python's standard
[https://docs.python.org/library/datetime.html#datetime.datetime|datetime]
objects can be used both in input and output. In input, they are recognized
automatically, and in output it is possible to get them by using the ``datetime``
value with the ``result_format`` argument.

One nice benefit with datetime objects is that they have different time
components available as attributes that can be easily accessed using the
extended variable syntax.

Examples:
| ${datetime} = | Convert Date | 2014-06-11 10:07:42.123 | datetime |
| Should Be Equal As Integers | ${datetime.year}        | 2014   |
| Should Be Equal As Integers | ${datetime.month}       | 6      |
| Should Be Equal As Integers | ${datetime.day}         | 11     |
| Should Be Equal As Integers | ${datetime.hour}        | 10     |
| Should Be Equal As Integers | ${datetime.minute}      | 7      |
| Should Be Equal As Integers | ${datetime.second}      | 42     |
| Should Be Equal As Integers | ${datetime.microsecond} | 123000 |

== Python date ==

Python's standard [https://docs.python.org/library/datetime.html#datetime.date|date]
objects are automatically recognized in input starting from Robot Framework 7.0.
They are not supported in output, but ``datetime`` objects can be converted
to ``date`` objects if needed:

| ${datetime} = | Convert Date | 2023-12-18 11:10:42 | datetime |
| Log | ${datetime.date()} | # The time part is ignored. |

== Epoch time ==

Epoch time is the time in seconds since the
[http://en.wikipedia.org/wiki/Unix_time|UNIX epoch] i.e. 00:00:00.000 (UTC)
January 1, 1970. To give a date as an epoch time, it must be given as a number
(integer or float), not as a string. To return a date as an epoch time,
it is possible to use ``epoch`` value with ``result_format`` argument.
Epoch times are returned as floating point numbers.

Notice that epoch times are independent on time zones and thus same
around the world at a certain time. For example, epoch times returned
by `Get Current Date` are not affected by the ``time_zone`` argument.
What local time a certain epoch time matches then depends on the time zone.

Following examples demonstrate using epoch times. They are tested in Finland,
and due to the reasons explained above they would fail on other time zones.

| ${date} =       | Convert Date | ${1000000000}           |
| Should Be Equal | ${date}      | 2001-09-09 04:46:40.000 |
| ${date} =       | Convert Date | 2014-06-12 13:27:59.279 | epoch |
| Should Be Equal | ${date}      | ${1402568879.279}       |

== Earliest supported date ==

The earliest date that is supported depends on the date format and to some
extent on the platform:

- Timestamps support year 1900 and above.
- Python datetime objects support year 1 and above.
- Epoch time supports 1970 and above on Windows.
- On other platforms epoch time supports 1900 and above or even earlier.

= Time formats =

Similarly as dates, times can be given to and received from keywords in
various different formats. Supported formats are `number`, `time string`
(verbose and compact), `timer string` and `Python timedelta`.

Input format for time is always determined automatically based on the input.
Result format is number by default, but it can be customised using
``result_format`` argument.

== Number ==

Time given as a number is interpreted to be seconds. It can be given
either as an integer or a float, or it can be a string that can be converted
to a number.

To return a time as a number, ``result_format`` argument must have value
``number``, which is also the default. Returned number is always a float.

Examples:
| ${time} =       | Convert Time | 3.14    |
| Should Be Equal | ${time}      | ${3.14} |
| ${time} =       | Convert Time | ${time} | result_format=number |
| Should Be Equal | ${time}      | ${3.14} |

== Time string ==

Time strings are strings in format like ``1 minute 42 seconds`` or ``1min 42s``.
The basic idea of this format is having first a number and then a text
specifying what time that number represents. Numbers can be either
integers or floating point numbers, the whole format is case and space
insensitive, and it is possible to add a minus prefix to specify negative
times. The available time specifiers are:

- ``weeks``, ``week``, ``w`` (new in RF 7.1)
- ``days``, ``day``, ``d``
- ``hours``, ``hour``, ``h``
- ``minutes``, ``minute``, ``mins``, ``min``, ``m``
- ``seconds``, ``second``, ``secs``, ``sec``, ``s``
- ``milliseconds``, ``millisecond``, ``millis``, ``ms``
- ``microseconds``, ``microsecond``, ``us``, ``μs`` (new in RF 6.0)
- ``nanoseconds``, ``nanosecond``, ``ns`` (new in RF 6.0)

When returning a time string, it is possible to select between ``verbose``
and ``compact`` representations using ``result_format`` argument. The verbose
format uses long specifiers ``week``, ``day``, ``hour``, ``minute``, ``second`` and
``millisecond``, and adds ``s`` at the end when needed. The compact format uses
shorter specifiers ``w``, ``d``, ``h``, ``min``, ``s`` and ``ms``, and even drops
the space between the number and the specifier.

Examples:
| ${time} =       | Convert Time | 1 minute 42 seconds |
| Should Be Equal | ${time}      | ${102}              |
| ${time} =       | Convert Time | 4200                | verbose |
| Should Be Equal | ${time}      | 1 hour 10 minutes   |
| ${time} =       | Convert Time | - 1.5 hours         | compact |
| Should Be Equal | ${time}      | - 1h 30min          |

== Timer string ==

Timer string is a string given in timer like format ``hh:mm:ss.mil``. In this
format both hour and millisecond parts are optional, leading and trailing
zeros can be left out when they are not meaningful, and negative times can
be represented by adding a minus prefix.

To return a time as timer string, ``result_format`` argument must be given
value ``timer``. Timer strings are by default returned in full ``hh:mm:ss.mil``
format, but milliseconds can be excluded using ``exclude_millis`` as explained
in `Millisecond handling` section.

Examples:
| ${time} =       | Convert Time | 01:42        |
| Should Be Equal | ${time}      | ${102}       |
| ${time} =       | Convert Time | 01:10:00.123 |
| Should Be Equal | ${time}      | ${4200.123}  |
| ${time} =       | Convert Time | 102          | timer |
| Should Be Equal | ${time}      | 00:01:42.000 |
| ${time} =       | Convert Time | -101.567     | timer | exclude_millis=yes |
| Should Be Equal | ${time}      | -00:01:42    |

== Python timedelta ==

Python's standard
[http://docs.python.org/library/datetime.html#datetime.timedelta|timedelta]
objects are also supported both in input and in output. In input they are
recognized automatically, and in output it is possible to receive them by
giving ``timedelta`` value to ``result_format`` argument.

Examples:
| ${timedelta} =  | Convert Time                 | 01:10:02.123 | timedelta |
| Should Be Equal | ${timedelta.total_seconds()} | ${4202.123}  |

= Millisecond handling =

This library handles dates and times internally using the precision of the
given input. With `timestamp`, `time string`, and `timer string` result
formats seconds are, however, rounded to millisecond accuracy. Milliseconds
may also be included even if there would be none.

All keywords returning dates or times have an option to leave milliseconds out
by giving a true value to ``exclude_millis`` argument. If the argument is given
as a string, it is considered true unless it is empty or case-insensitively
equal to ``false``, ``none`` or ``no``. Other argument types are tested using
same [http://docs.python.org/library/stdtypes.html#truth|rules as in
Python].

When milliseconds are excluded, seconds in returned dates and times are
rounded to the nearest full second. With `timestamp` and `timer string`
result formats, milliseconds will also be removed from the returned string
altogether.

Examples:
| ${date} =       | Convert Date | 2014-06-11 10:07:42     |
| Should Be Equal | ${date}      | 2014-06-11 10:07:42.000 |
| ${date} =       | Convert Date | 2014-06-11 10:07:42.500 | exclude_millis=yes |
| Should Be Equal | ${date}      | 2014-06-11 10:07:43     |
| ${dt} =         | Convert Date | 2014-06-11 10:07:42.500 | datetime | exclude_millis=yes |
| Should Be Equal | ${dt.second} | ${43}        |
| Should Be Equal | ${dt.microsecond} | ${0}    |
| ${time} =       | Convert Time | 102          | timer | exclude_millis=false |
| Should Be Equal | ${time}      | 00:01:42.000 |       |
| ${time} =       | Convert Time | 102.567      | timer | exclude_millis=true |
| Should Be Equal | ${time}      | 00:01:43     |       |

= Programmatic usage =

In addition to be used as normal library, this library is intended to
provide a stable API for other libraries to use if they want to support
same date and time formats as this library. All the provided keywords
are available as functions that can be easily imported:

| from robot.libraries.DateTime import convert_time
|
| def example_keyword(timeout):
|     seconds = convert_time(timeout)
|     # ...

Additionally, helper classes ``Date`` and ``Time`` can be used directly:

| from robot.libraries.DateTime import Date, Time
|
| def example_keyword(date, interval):
|     date = Date(date).convert('datetime')
|     interval = Time(interval).convert('number')
|     # ...
"""

import datetime
import sys
import time
from typing import Any

from robot.utils import (
    elapsed_time_to_string, secs_to_timestr, timestr_to_secs, type_name
)
from robot.version import get_version

__version__ = get_version()
__all__ = [
    "add_time_to_date",
    "add_time_to_time",
    "convert_date",
    "convert_time",
    "get_current_date",
    "subtract_date_from_date",
    "subtract_time_from_date",
    "subtract_time_from_time",
]


def get_current_date(
    time_zone="local",
    increment=0,
    result_format="timestamp",
    exclude_millis=False,
):
    """Returns current local or UTC time with an optional increment.

    Arguments:
    - ``time_zone:``      Get the current time on this time zone. Currently only
                          ``local`` (default) and ``UTC`` are supported.
                          Has no effect if date is returned as an `epoch time`.
    - ``increment:``      Optional time increment to add to the returned date in
                          one of the supported `time formats`. Can be negative.
    - ``result_format:``  Format of the returned date (see `date formats`).
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.

    Examples:
    | ${date} =       | Get Current Date |
    | Should Be Equal | ${date}          | 2014-06-12 20:00:58.946 |
    | ${date} =       | Get Current Date | UTC                     |
    | Should Be Equal | ${date}          | 2014-06-12 17:00:58.946 |
    | ${date} =       | Get Current Date | increment=02:30:00      |
    | Should Be Equal | ${date}          | 2014-06-12 22:30:58.946 |
    | ${date} =       | Get Current Date | UTC                     | - 5 hours |
    | Should Be Equal | ${date}          | 2014-06-12 12:00:58.946 |
    | ${date} =       | Get Current Date | result_format=datetime  |
    | Should Be Equal | ${date.year}     | ${2014}                 |
    | Should Be Equal | ${date.month}    | ${6}                    |
    """
    if time_zone.upper() == "LOCAL" or result_format.upper() == "EPOCH":
        dt = datetime.datetime.now()
    elif time_zone.upper() == "UTC":
        if sys.version_info >= (3, 12):
            # `utcnow()` was deprecated in Python 3.12. We only support "naive"
            # datetime objects and thus need to remove timezone information here.
            dt = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        else:
            dt = datetime.datetime.utcnow()
    else:
        raise ValueError(f"Unsupported timezone '{time_zone}'.")
    date = Date(dt) + Time(increment)
    return date.convert(result_format, millis=not exclude_millis)


def convert_date(
    date,
    result_format="timestamp",
    exclude_millis=False,
    date_format=None,
) -> "datetime|float":
    """Converts between supported `date formats`.

    Arguments:
    - ``date:``           Date in one of the supported `date formats`.
    - ``result_format:``  Format of the returned date.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.
    - ``date_format:``    Specifies possible `custom timestamp` format.

    Examples:
    | ${date} =       | Convert Date | 20140528 12:05:03.111   |
    | Should Be Equal | ${date}      | 2014-05-28 12:05:03.111 |
    | ${date} =       | Convert Date | ${date}                 | epoch |
    | Should Be Equal | ${date}      | ${1401267903.111}       |
    | ${date} =       | Convert Date | 5.28.2014 12:05         | exclude_millis=yes | date_format=%m.%d.%Y %H:%M |
    | Should Be Equal | ${date}      | 2014-05-28 12:05:00     |
    """
    return Date(date, date_format).convert(result_format, millis=not exclude_millis)


def convert_time(time, result_format="number", exclude_millis=False) -> Any:
    """Converts between supported `time formats`.

    Arguments:
    - ``time:``           Time in one of the supported `time formats`.
    - ``result_format:``  Format of the returned time.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.

    Examples:
    | ${time} =       | Convert Time  | 10 seconds        |
    | Should Be Equal | ${time}       | ${10}             |
    | ${time} =       | Convert Time  | 1:00:01           | verbose |
    | Should Be Equal | ${time}       | 1 hour 1 second   |
    | ${time} =       | Convert Time  | ${3661.5} | timer | exclude_milles=yes |
    | Should Be Equal | ${time}       | 01:01:02          |
    """
    return Time(time).convert(result_format, millis=not exclude_millis)


def subtract_date_from_date(
    date1,
    date2,
    result_format="number",
    exclude_millis=False,
    date1_format=None,
    date2_format=None,
) -> Any:
    """Subtracts date from another date and returns time between.

    Arguments:
    - ``date1:``          Date to subtract another date from in one of the
                          supported `date formats`.
    - ``date2:``          Date that is subtracted in one of the supported
                          `date formats`.
    - ``result_format:``  Format of the returned time (see `time formats`).
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.
    - ``date1_format:``   Possible `custom timestamp` format of ``date1``.
    - ``date2_format:``   Possible `custom timestamp` format of ``date2``.

     Examples:
    | ${time} =       | Subtract Date From Date | 2014-05-28 12:05:52     | 2014-05-28 12:05:10 |
    | Should Be Equal | ${time}                 | ${42}                   |
    | ${time} =       | Subtract Date From Date | 2014-05-28 12:05:52     | 2014-05-27 12:05:10 | verbose |
    | Should Be Equal | ${time}                 | 1 day 42 seconds        |
    """
    time = Date(date1, date1_format) - Date(date2, date2_format)
    return time.convert(result_format, millis=not exclude_millis)


def add_time_to_date(
    date,
    time,
    result_format="timestamp",
    exclude_millis=False,
    date_format=None,
) -> "datetime|float":
    """Adds time to date and returns the resulting date.

    Arguments:
    - ``date:``           Date to add time to in one of the supported
                          `date formats`.
    - ``time:``           Time that is added in one of the supported
                          `time formats`.
    - ``result_format:``  Format of the returned date.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.
    - ``date_format:``    Possible `custom timestamp` format of ``date``.

    Examples:
    | ${date} =       | Add Time To Date | 2014-05-28 12:05:03.111 | 7 days       |
    | Should Be Equal | ${date}          | 2014-06-04 12:05:03.111 |              |
    | ${date} =       | Add Time To Date | 2014-05-28 12:05:03.111 | 01:02:03:004 |
    | Should Be Equal | ${date}          | 2014-05-28 13:07:06.115 |
    """
    date = Date(date, date_format) + Time(time)
    return date.convert(result_format, millis=not exclude_millis)


def subtract_time_from_date(
    date,
    time,
    result_format="timestamp",
    exclude_millis=False,
    date_format=None,
) -> Any:
    """Subtracts time from date and returns the resulting date.

    Arguments:
    - ``date:``           Date to subtract time from in one of the supported
                          `date formats`.
    - ``time:``           Time that is subtracted in one of the supported
                         `time formats`.
    - ``result_format:``  Format of the returned date.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.
    - ``date_format:``    Possible `custom timestamp` format of ``date``.

    Examples:
    | ${date} =       | Subtract Time From Date | 2014-06-04 12:05:03.111 | 7 days |
    | Should Be Equal | ${date}                 | 2014-05-28 12:05:03.111 |
    | ${date} =       | Subtract Time From Date | 2014-05-28 13:07:06.115 | 01:02:03:004 |
    | Should Be Equal | ${date}                 | 2014-05-28 12:05:03.111 |
    """
    date = Date(date, date_format) - Time(time)
    return date.convert(result_format, millis=not exclude_millis)


def add_time_to_time(time1, time2, result_format="number", exclude_millis=False) -> Any:
    """Adds time to another time and returns the resulting time.

    Arguments:
    - ``time1:``          First time in one of the supported `time formats`.
    - ``time2:``          Second time in one of the supported `time formats`.
    - ``result_format:``  Format of the returned time.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.

    Examples:
    | ${time} =       | Add Time To Time | 1 minute          | 42       |
    | Should Be Equal | ${time}          | ${102}            |
    | ${time} =       | Add Time To Time | 3 hours 5 minutes | 01:02:03 | timer | exclude_millis=yes |
    | Should Be Equal | ${time}          | 04:07:03          |
    """
    time = Time(time1) + Time(time2)
    return time.convert(result_format, millis=not exclude_millis)


def subtract_time_from_time(
    time1, time2, result_format="number", exclude_millis=False
) -> Any:
    """Subtracts time from another time and returns the resulting time.

    Arguments:
    - ``time1:``          Time to subtract another time from in one of
                          the supported `time formats`.
    - ``time2:``          Time to subtract in one of the supported `time formats`.
    - ``result_format:``  Format of the returned time.
    - ``exclude_millis:`` When set to any true value, rounds and drops
                          milliseconds as explained in `millisecond handling`.

    Examples:
    | ${time} =       | Subtract Time From Time | 00:02:30 | 100      |
    | Should Be Equal | ${time}                 | ${50}    |
    | ${time} =       | Subtract Time From Time | ${time}  | 1 minute | compact |
    | Should Be Equal | ${time}                 | - 10s    |
    """
    time = Time(time1) - Time(time2)
    return time.convert(result_format, millis=not exclude_millis)


class Date:

    def __init__(self, date, input_format=None):
        self.datetime = self._convert_to_datetime(date, input_format)

    @property
    def seconds(self):
        # Mainly for backwards compatibility with RF 2.9.1 and earlier.
        return self._convert_to_epoch(self.datetime)

    def _convert_to_datetime(self, date, input_format):
        if isinstance(date, datetime.datetime):
            return date
        if isinstance(date, datetime.date):
            return datetime.datetime(date.year, date.month, date.day)
        if isinstance(date, (int, float)):
            return self._epoch_seconds_to_datetime(date)
        if isinstance(date, str):
            return self._string_to_datetime(date, input_format)
        raise ValueError(f"Unsupported input '{date}'.")

    def _epoch_seconds_to_datetime(self, secs):
        return datetime.datetime.fromtimestamp(secs)

    def _string_to_datetime(self, ts, input_format):
        if not input_format:
            ts = self._normalize_timestamp(ts)
            input_format = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.datetime.strptime(ts, input_format)

    def _normalize_timestamp(self, timestamp):
        numbers = "".join(d for d in timestamp if d.isdigit())
        if not (8 <= len(numbers) <= 20):
            raise ValueError(f"Invalid timestamp '{timestamp}'.")
        d = numbers[:8]
        t = numbers[8:].ljust(12, "0")
        return f"{d[:4]}-{d[4:6]}-{d[6:8]} {t[:2]}:{t[2:4]}:{t[4:6]}.{t[6:]}"

    def convert(self, format, millis=True):
        dt = self.datetime
        if not millis:
            secs = 1 if dt.microsecond >= 5e5 else 0
            dt = dt.replace(microsecond=0) + datetime.timedelta(seconds=secs)
        if "%" in format:
            return self._convert_to_custom_timestamp(dt, format)
        format = format.lower()
        if format == "timestamp":
            return self._convert_to_timestamp(dt, millis)
        if format == "datetime":
            return dt
        if format == "epoch":
            return self._convert_to_epoch(dt)
        raise ValueError(f"Unknown format '{format}'.")

    def _convert_to_custom_timestamp(self, dt, format):
        return dt.strftime(format)

    def _convert_to_timestamp(self, dt, millis=True):
        if not millis:
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        ms = round(dt.microsecond / 1000)
        if ms == 1000:
            dt += datetime.timedelta(seconds=1)
            ms = 0
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{ms:03d}"

    def _convert_to_epoch(self, dt):
        try:
            return dt.timestamp()
        except OSError:
            # https://github.com/python/cpython/issues/81708
            return time.mktime(dt.timetuple()) + dt.microsecond / 1e6

    def __add__(self, other):
        if isinstance(other, Time):
            return Date(self.datetime + other.timedelta)
        raise TypeError(f"Can only add Time to Date, got {type_name(other)}.")

    def __sub__(self, other):
        if isinstance(other, Date):
            return Time(self.datetime - other.datetime)
        if isinstance(other, Time):
            return Date(self.datetime - other.timedelta)
        raise TypeError(
            f"Can only subtract Date or Time from Date, got {type_name(other)}."
        )


class Time:

    def __init__(self, time):
        self.seconds = float(self._convert_time_to_seconds(time))

    def _convert_time_to_seconds(self, time):
        if isinstance(time, datetime.timedelta):
            return time.total_seconds()
        return timestr_to_secs(time, round_to=None)

    @property
    def timedelta(self):
        return datetime.timedelta(seconds=self.seconds)

    def convert(self, format, millis=True):
        try:
            result_converter = getattr(self, f"_convert_to_{format.lower()}")
        except AttributeError:
            raise ValueError(f"Unknown format '{format}'.")
        seconds = self.seconds if millis else float(round(self.seconds))
        return result_converter(seconds, millis)

    def _convert_to_number(self, seconds, millis=True):
        return seconds

    def _convert_to_verbose(self, seconds, millis=True):
        return secs_to_timestr(seconds)

    def _convert_to_compact(self, seconds, millis=True):
        return secs_to_timestr(seconds, compact=True)

    def _convert_to_timer(self, seconds, millis=True):
        return elapsed_time_to_string(seconds, include_millis=millis, seconds=True)

    def _convert_to_timedelta(self, seconds, millis=True):
        return datetime.timedelta(seconds=seconds)

    def __add__(self, other):
        if isinstance(other, Time):
            return Time(self.seconds + other.seconds)
        raise TypeError(f"Can only add Time to Time, got {type_name(other)}.")

    def __sub__(self, other):
        if isinstance(other, Time):
            return Time(self.seconds - other.seconds)
        raise TypeError(f"Can only subtract Time from Time, got {type_name(other)}.")
