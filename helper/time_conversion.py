"""This module contains functions for converting values of year, month, day, hour, minute, seconds
into a single value of seconds since 1st January 2000 00:00 AM.
"""


def is_leap_year(year):
    """Check whether year is a leap year, return bool"""
    is_leap = False
    if year % 4 == 0:
        is_leap = True
        if year % 100 == 0:
            is_leap = False
            if year % 400 == 0:
                is_leap = True
    return is_leap


def convert_to_sec(year, month, day, hour, minute, second):
    """Convert ymdhms into seconds from 1st January 2000 00:00 AM, return int"""
    total_sec = 0
    # calculate seconds for all but last year
    for yr in range(2000, year):
        total_sec += 365 * 24 * 3600
        if is_leap_year(yr):
            total_sec += 24 * 3600
    # only current year calculation remaining
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(year):
        month_days[1] = 29
    if month > 1:
        for mon in range(month - 1):
            total_sec += month_days[mon] * 24 * 3600
    # only current month calculation remaining
    total_sec += (day - 1) * 24 * 3600 + hour * 3600 + minute * 60 + second
    return total_sec
