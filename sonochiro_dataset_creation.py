"""Python module for turning SonoChiro output into a functional datafile (csv format) for the
Light on Nature project. By Hugo Loning, 2016
"""

from collections import defaultdict
import re
import time


# SonoChiro output line regular expression functions


def is_valid_filename(filename):
    """Check whether supplied filename is one of the two common types, not an abberation or header, return bool"""
    match = re.search(r'([0-9]{8})_[0-9]+|([a-zA-Z]{3}([a-zA-Z])*?20[0-9]{2})', filename)
    if match is None or filename.startswith("20130827"):  # wrong filename or the rename mistake at 2013-8-27
        return False
    return True


def extract_time(filename):
    """Extract time parameters of a filename and return a list containing ymdhms"""
    match = re.search(r'([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})', filename)
    return [int(elem) for elem in match.group(1, 2, 3, 4, 5, 6)]


def extract_tr_d_cf(filename):
    """Extracts transect, detector and compact flash card from filename and return a tuple.
    Corrected for all present (September 2016) typos and periphery experiment 2012 data.
    """
    # one typo with transect indicated as tr_## instead of tr##;
    # periphery experiment has an additional c or C which will not be written to output dataset
    transect = int(re.search(r'tr[_]*?([0-9]+)[cC]*?_', filename).group(1))
    detector_match = re.search(r'd([0-9]+)_', filename)
    if detector_match is not None:  # there is a typo where detector is indicated as number without d in front of it
        detector = int(detector_match.group(1))
    else:
        detector = int(re.search(r'tr[0-9]+_([0-9]+)_cf', filename).group(1))
    comp_fl = re.search(r'cf([0-9]+[aA]*?)_', filename).group(1)  # one flash card has an 'a' at the end of the number
    return transect, detector, comp_fl


def extract_species_sound(line):
    """Extract all classification parameters from splitted sonochiro output line and return them in a list"""
    final_id, contact, group, group_index, species, species_index = line[2:8]
    group_index, species_index = int(group_index), int(species_index)
    nb_calls, med_freq, med_int, i_qual, i_sc, i_buzz = [int(elem) for elem in line[17:]]
    return [final_id, contact, group, group_index, species, species_index,
            nb_calls, med_freq, med_int, i_qual, i_sc, i_buzz]


# Time conversion functions


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


# Helper file loading + lookup functions


def load_transects_array():
    """Return a dictionary (transects:[site,colour]) of the transects.csv file which should be in the same directory"""
    transects = defaultdict(list)
    with open("transects.csv") as input_file:
        for line in input_file:
            transect, site, name, colour = [elem.isdigit() and int(elem) or elem for elem in line.split(',')[:4]]
            transects[transect].extend([site, colour])
    return dict(transects)


def load_sun_data_array():
    """Return a list containing converted time of noon of the SunData.csv file which should be in the same directory"""
    sun_data = []
    with open("SunData.csv") as input_file:
        for line in input_file:
            match = re.search(r'(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+),\d+/\d+/\d+ (\d+):(\d+):(\d+)\n', line)
            year, month, day, dawn_h, dawn_m, dawn_s, dusk_h, dusk_m, dusk_s = [int(elem) for elem in
                                                                                match.group(3, 1, 2, 4, 5, 6, 7, 8, 9)]
            dawn_in_sec = dawn_h * 3600 + dawn_m * 60 + dawn_s
            dusk_in_sec = dusk_h * 3600 + dusk_m * 60 + dusk_s
            noon_in_sec = (dawn_in_sec + dusk_in_sec) // 2  # this is floor division (so we get int back)
            noon_h = noon_in_sec // 3600
            noon_m = (noon_in_sec - noon_h * 3600) // 60
            noon_s = noon_in_sec - noon_h * 3600 - noon_m * 60
            noon_converted_to_sec = convert_to_sec(year, month, day, noon_h, noon_m, noon_s)
            sun_data.append(noon_converted_to_sec)  # make entry in array
    return sun_data


def lookup_sun_data_array(sun_data_array, converted_entry):
    """Lookup which night since 1st January 2012 belongs to ymdhms converted to sec entered, return int.
    First night in sun_data_array is 31th Dec 2011."""
    for night, sun_data_entry in enumerate(sun_data_array):
        if converted_entry < sun_data_entry:
            return night


def load_allowed_nights():
    """Return a dictionary (site:allowed nights) as values of the 2012-2016allowednights.csv file
    which should be in the same directory.
    """
    allowed = defaultdict(list)  # create a dictionary with an empty list for every key
    with open("2012-2016_allowednights.csv") as input_file:
        for line in input_file:
            site, night = [int(elem) for elem in line.split(",")[:2]]
            allowed[site].append(night)
    return dict(allowed)


def load_lights_off(sun_data_array):
    """Return a dictionary (site:nights with lights off) of the loglightsoff.csv file which should
    be in the same directory.
    """
    site_codes = {'lbh': [1], 'vst': [2], 'rko': [3], 'ask': [4, 5], 'kla': [6, 7], 'hkv': [8]}
    light_off = defaultdict(list)  # create dictionary with for each entry an empty list
    with open("loglightsoff.csv") as input_file:
        for line in input_file:
            date, site_code, lights, remarks = line.strip().split(",")
            if lights == 'off':  # only execute code if the lights were off
                month, day, year = [int(elem) for elem in date.split("/")]
                converted = convert_to_sec(year, month, day, 23, 0, 0)
                night = lookup_sun_data_array(sun_data_array, converted)
                for site in site_codes[site_code]:
                    light_off[site].append(night)
    return dict(light_off)


# Main loading and writing function


def load_sonochiro_file(sonochiro_file):
    """Load a sonochiro output file to a complete dataset array with all important information available.
    Return a tuple of length 4 with the array, header names as list, dictionary with skipped entries and count
    as int of files excluded because they were not recorded during an allowed night or the lights were off.
    """
    sun_data = load_sun_data_array()
    lights_off = load_lights_off(sun_data)
    tr_array = load_transects_array()
    allowed_nights = load_allowed_nights()
    sonochiro_array = []
    skip_dict = {}  # keep track of entries skipped, using linecounter
    excluded_total = 0  # count files that will be excluded_total because they are not an allowed night
    with open(sonochiro_file) as sonochiro:
        for linecounter, line in enumerate(sonochiro):
            line = line.strip().split(",")
            filename = line[1]
            if not is_valid_filename(filename):  # skip files with invalid filenames, this includes headers
                if line[0] == "Directory":
                    skip_dict[linecounter] = "Header"
                else:
                    skip_dict[linecounter] = filename
                continue
            year, month, day, hour, minute, second = extract_time(filename)
            total_time_sec = convert_to_sec(year, month, day, hour, minute, second)
            night = lookup_sun_data_array(sun_data, total_time_sec)
            transect, detector, comp_fl = extract_tr_d_cf(filename)
            site, colour = tr_array[transect]
            if night not in allowed_nights[site] or night in lights_off[site]:
                excluded_total += 1
                continue
            entry = [filename, transect, site, colour, night, total_time_sec, detector, comp_fl]
            entry.extend(extract_species_sound(line))
            sonochiro_array.append(entry)
    name_of_column = ['filename', 'transect', 'site', 'colour', 'night', 'total_time_sec', 'detector', 'comp_fl',
                      'final_id', 'contact', 'group', 'group_index', 'species', 'species_index',
                      'nb_calls', 'med_freq', 'med_int', 'i_qual', 'i_sc', 'i_buzz']
    return sonochiro_array, name_of_column, skip_dict, excluded_total


def write_array(array, header_names, output_file):
    """Write a two-dimensional array with header made from header_names to a specified csv file"""
    with open(output_file, "w") as output:
        output.write(",".join(header_names) + "\n")  # write header
        for row in array:
            output.write(",".join([str(element) for element in row]) + "\n")  # write rows


# The actual script is here
if __name__ == "__main__":
    # Specify input (to load) and output (to write) file
    file_to_load = "sonochiro_output_all.csv"
    file_to_write = "dataset_sonochiro.csv"

    # The script
    print("SONOCHIRO DATA CREATION SCRIPT FOR LIGHT ON NATURE BY HUGO LONING 2016\n")
    print("Loading " + file_to_load + "...\n")
    start_time = time.time()  # measure time to complete program
    sc, column_names, skipped, excluded = load_sonochiro_file(file_to_load)
    print("Loaded in %.1f seconds, of %d total entries, %d entries were unusable\n"
          "and skipped, %d entries were in nights with lights off or in nights that\n"
          "did not have all detectors running and were excluded.\n" % (time.time() - start_time,
                                                                       len(sc) + len(skipped) + excluded,
                                                                       len(skipped), excluded))
    print("Writing " + file_to_write + "...\n")
    start_time2 = time.time()
    write_array(sc, column_names, file_to_write)
    print("Written in %.1f seconds, total run time %.1f seconds, type \'skipped\' for \n"
          "a dictionary (line:filename) of the entries skipped during file loading." % (time.time() - start_time2,
                                                                                        time.time() - start_time))
