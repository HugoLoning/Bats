"""This module contains functions for loading data files that are used for supplementary information in many of
the other modules.
"""

import re
from collections import defaultdict
from helper.time_conversion import convert_to_sec


def load_transects():
    """Return a dictionary (transects:[site,colour]) of the transects.csv file"""
    transects = defaultdict(list)
    with open("helper\\transects.csv") as input_file:
        for line in input_file:
            transect, site, name, colour = [elem.isdigit() and int(elem) or elem for elem in line.split(',')[:4]]
            transects[transect].extend([site, colour])
    return dict(transects)


def load_sun_data():
    """Return a list containing converted time of noon of the SunData.csv file"""
    sun_data = []
    with open("helper\\SunData.csv") as input_file:
        for line in input_file:
            match = re.search(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+),\d+/\d+/\d+ (\d+):(\d+):(\d+)\n', line)
            month, day, year, dawn_h, dawn_m, dawn_s, dusk_h, dusk_m, dusk_s = [int(elem) for elem in match.groups()]
            dawn_in_sec = dawn_h * 3600 + dawn_m * 60 + dawn_s
            dusk_in_sec = dusk_h * 3600 + dusk_m * 60 + dusk_s
            noon_in_sec = (dawn_in_sec + dusk_in_sec) // 2  # this is floor division (so we get int back)
            noon_h = noon_in_sec // 3600
            noon_m = (noon_in_sec - noon_h * 3600) // 60
            noon_s = noon_in_sec - noon_h * 3600 - noon_m * 60
            noon_converted_to_sec = convert_to_sec(year, month, day, noon_h, noon_m, noon_s)
            sun_data.append(noon_converted_to_sec)  # make entry in array
    return sun_data


def lookup_sun_data(sun_data_array, converted_entry):
    """Lookup which night since 1st January 2012 belongs to ymdhms converted to sec entered, return int.
    First night in sun_data_array is 31th Dec 2011."""
    for night, sun_data_entry in enumerate(sun_data_array):
        if converted_entry < sun_data_entry:
            return night


def load_allowed_nights():
    """Return a dictionary (site:allowed nights) as values of the 2012-2016allowednights.csv file"""
    allowed = defaultdict(list)  # create a dictionary with an empty list for every key
    with open("helper\\2012-2016_allowednights.csv") as input_file:
        for line in input_file:
            site, night = [int(elem) for elem in line.split(",")[:2]]
            allowed[site].append(night)
    return dict(allowed)


def load_lights_off(sun_data_array):
    """Return a dictionary (site:nights with lights off) of the loglightsoff.csv file"""
    site_codes = {'lbh': [1], 'vst': [2], 'rko': [3], 'ask': [4, 5], 'kla': [6, 7], 'hkv': [8]}
    light_off = defaultdict(list)  # create dictionary with for each entry an empty list
    with open("helper\\loglightsoff.csv") as input_file:
        for line in input_file:
            date, site_code, lights, remarks = line.strip().split(",")
            if lights == 'off':  # only execute code if the lights were off
                month, day, year = [int(elem) for elem in date.split("/")]
                converted = convert_to_sec(year, month, day, 23, 0, 0)
                night = lookup_sun_data(sun_data_array, converted)
                for site in site_codes[site_code]:
                    light_off[site].append(night)
    return dict(light_off)
