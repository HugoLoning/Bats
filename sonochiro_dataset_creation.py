"""Python module for turning SonoChiro output into a functional datafile (csv format) for the
Light on Nature project. By Hugo Loning, 2016
"""

import re
import time

# SonoChiro output line regular expression functions


def is_valid_filename(filename):
    """Check whether supplied filename is one of the two common types, not an abberation or header, return bool"""
    filename_matcher = re.compile(r'([0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])_[0-9]+|'
                                  r'([a-zA-Z][a-zA-Z][a-zA-Z]([a-zA-Z])*?20[0-9][0-9])')
    filename_match = filename_matcher.search(filename)
    valid = True
    if filename_match is None or filename.startswith("20130827"):  # wrong filename or the rename mistake at 2013-8-27
        valid = False
    return valid


def extract_time(filename):
    """Extract time parameters of a filename and return a list containing ymdhms"""
    time_matcher = re.compile(r'([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])_([0-9][0-9])([0-9][0-9])([0-9][0-9])')
    time_match = time_matcher.search(filename)
    return [int(elem) for elem in time_match.group(1, 2, 3, 4, 5, 6)]


def extract_tr_d_cf(filename):
    """Extracts transect, detector and compact flash card from filename and return a tuple.
    Corrected for all present (September 2016) typos and periphery experiment 2012 data.
    """
    tr_matcher = re.compile(r'tr[_]*?([0-9]+)[cC]*?_')
    # one typo with transect indicated as tr_## instead of tr##;
    # periphery experiment has an additional c or C which will not be written to output dataset
    tr_match = tr_matcher.search(filename)
    transect = int(tr_match.group(1))
    d_matcher = re.compile(r'd([0-9]+)_')
    d_match = d_matcher.search(filename)
    if d_match is not None:  # there is a typo where detector is indicated as number without d in front of it
        detector = int(d_match.group(1))
    else:
        typo_matcher = re.compile(r'tr[0-9]+_([0-9]+)_cf')
        typo_match = typo_matcher.search(filename)
        detector = int(typo_match.group(1))
    cf_matcher = re.compile(r'cf([0-9]+[aA]*?)_')  # one flash card has an 'a' at the end of the number
    cf_match = cf_matcher.search(filename)
    comp_fl = cf_match.group(1)
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
        total_sec += 365*24*3600
        if is_leap_year(yr):
            total_sec += 24*3600
    # only current year calculation remaining
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(year):
        month_days[1] = 29
    if month > 1:
        for mon in range(month-1):
            total_sec += month_days[mon]*24*3600
    # only current month calculation remaining
    total_sec += (day-1)*24*3600 + hour*3600 + minute*60 + second
    return total_sec


# Helper file loading + lookup functions


def load_transects_array():
    """Return an array of the transects.csv file which should be in the same directory"""
    transects = []
    with open("transects.csv") as input_file:
        for line in input_file:
            line_matcher = re.compile(r'([0-9]+),([0-9]+),(.+?),([a-z]+),([0-9]+?)-([0-9]+?)-([0-9]+?)\n')
            line_match = line_matcher.search(line)
            transect, site, start_year, start_month, start_day = [int(elem) for elem in line_match.group(1, 2, 5, 6, 7)]
            name, colour = line_match.group(3, 4)
            transects += [[transect, site, name, colour, start_year, start_month, start_day]]
    return transects


def load_sun_data_array():
    """Return an array of the SunData.csv file which should be in the same directory"""
    sun_data = []
    with open("SunData.csv") as input_file:
        for line in input_file:
            line_matcher = re.compile(r'([0-9]+)/([0-9]+)/([0-9]+) ([0-9]+):([0-9]+):([0-9]+),'
                                      + '[0-9]+/[0-9]+/[0-9]+ ([0-9]+):([0-9]+):([0-9]+)\n')
            line_match = line_matcher.search(line)
            year, month, day = [int(elem) for elem in line_match.group(3, 1, 2)]

            dawn_h, dawn_m, dawn_s = [int(elem) for elem in line_match.group(4, 5, 6)]
            dawn_in_sec = dawn_h*3600+dawn_m*60+dawn_s

            dusk_h, dusk_m, dusk_s = [int(elem) for elem in line_match.group(7, 8, 9)]
            dusk_in_sec = dusk_h*3600+dusk_m*60+dusk_s

            noon_in_sec = (dawn_in_sec+dusk_in_sec)//2  # this is floor division (so we get int back)
            noon_h = noon_in_sec//3600
            noon_m = (noon_in_sec-noon_h*3600)//60
            noon_s = noon_in_sec-noon_h*3600-noon_m*60

            noon_converted_to_sec = convert_to_sec(year, month, day, noon_h, noon_m, noon_s)
            sun_data += [noon_converted_to_sec]  # make entry in array
    return sun_data


def lookup_sun_data_array(sun_data_array, converted_entry):
    """Lookup which night since 1st January 2012 belongs to ymdhms converted to sec entered, return int"""
    night = 190  # first night in sun_data_array is 31th Dec 2011, start counting at 190 to save some loops
    while converted_entry > sun_data_array[night]:
        night += 1
    return night


def load_allowed_nights():
    """Return a dictionary (site:allowed nights) as values of the 2012-2016allowednights.csv file
    which should be in the same directory.
    """
    allowed = {}
    with open("2012-2016_allowednights.csv") as input_file:
        for line in input_file:
            line_list = line.split(",")
            site, night = int(line_list[0]), int(line_list[1])
            if site not in allowed:  # first time this site is encountered
                allowed[site] = [night]
            else:
                allowed[site] += [night]
    return allowed


def load_lights_off(sun_data_array):
    """Return a dictionary (site:nights with lights off) of the loglightsoff.csv file which should
    be in the same directory.
    """
    site_codes = {'lbh': [1], 'vst': [2], 'rko': [3], 'ask': [4, 5], 'kla': [6, 7], 'hkv': [8]}
    light_off = {}
    for site_nr in range(1, 9):  # create empty list of each site to hold all lights with lights off
        light_off[site_nr] = []
    with open("loglightsoff.csv") as input_file:
        for line in input_file:
            date, site_code, lights, remarks = line.strip().split(",")
            if lights == 'off':  # only execute code if the lights were off
                try:
                    month, day, year = [int(elem) for elem in date.split("/")]
                except ValueError:  # when it is the header, nothing will be splitted
                    continue
                converted = convert_to_sec(year, month, day, 23, 0, 0)
                night = lookup_sun_data_array(sun_data_array, converted)
                sites = site_codes[site_code]
                for site in sites:
                    light_off[site] += [night]
    return light_off


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
    linecounter = 0
    with open(sonochiro_file) as sonochiro:
        for line in sonochiro:
            linecounter += 1
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
            site, colour = tr_array[transect-1][1], tr_array[transect-1][3]
            if night not in allowed_nights[site] or night in lights_off[site]:
                excluded_total += 1
                continue
            entry = [filename, transect, site, colour, night, total_time_sec, detector, comp_fl]
            entry += extract_species_sound(line)
            sonochiro_array += [entry]
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
          "did not have all detectors running and were excluded.\n" % (time.time()-start_time,
                                                                       len(sc)+len(skipped)+excluded,
                                                                       len(skipped), excluded))
    print("Writing " + file_to_write + "...\n")
    start_time2 = time.time()
    write_array(sc, column_names, file_to_write)
    print("Written in %.1f seconds, total run time %.1f seconds, type \'skipped\' for \n"
          "a dictionary (line:filename) of the entries skipped during file loading." % (time.time()-start_time2,
                                                                                        time.time()-start_time))
