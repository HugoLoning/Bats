"""Python module for turning SonoChiro output into a functional datafile (csv format) for the
Light on Nature project. By Hugo Loning, 2016
"""

import re
import time

from helper.load_info import load_transects, load_sun_data, lookup_sun_data, load_allowed_nights, load_lights_off
from helper.time_conversion import convert_to_sec
from helper.write_data import write_array


def is_valid_filename(filename):
    """Check whether supplied filename is one of the two common types, not an abberation or header, return bool"""
    match = re.search(r'(\d{8}_\d+)|([a-zA-Z]{3}[a-zA-Z]*?20\d{2})', filename)
    if match is None or filename.startswith("20130827"):  # wrong filename or the rename mistake at 2013-8-27
        return False
    return True


def extract_time(filename):
    """Extract time parameters of a filename and return a list containing ymdhms"""
    return [int(elem) for elem in re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename).groups()]


def extract_tr_d_cf(filename):
    """Extracts transect, detector and compact flash card from filename and return a tuple.
    Corrected for all present (September 2016) typos and periphery experiment 2012 data.
    """
    transect = int(re.search(r'tr[_]*?(\d+)[cC]*?_', filename).group(1))
    # one typo with transect indicated as tr_## instead of tr##, periphery experiment has an additional c or C
    try:  # there is a typo where detector is indicated as number without d in front of it
        detector = int(re.search(r'd(\d+)_', filename).group(1))
    except AttributeError:  # if the typo is present, re.search will return None and None doesn't have group method
        detector = int(re.search(r'tr\d+_(\d+)_cf', filename).group(1))
    comp_fl = re.search(r'cf(\d+[aA]*?)_', filename).group(1)  # one flash card has an 'a' at the end of the number
    return transect, detector, comp_fl


def load_sonochiro_file(sonochiro_file):
    """Load a sonochiro output file to a complete dataset array with all important information available.
    Return a tuple of length 4 with the array, header names as list, dictionary with skipped entries and count
    as int of files excluded because they were not recorded during an allowed night or the lights were off.
    """
    sun_data = load_sun_data()
    lights_off = load_lights_off(sun_data)
    tr_array = load_transects()
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
            night = lookup_sun_data(sun_data, total_time_sec)
            transect, detector, comp_fl = extract_tr_d_cf(filename)
            site, colour = tr_array[transect]
            if night not in allowed_nights[site] or night in lights_off[site]:
                excluded_total += 1
                continue
            entry = [filename, transect, site, colour, night, total_time_sec, detector, comp_fl]
            entry.extend(line[2:8])  # add species classification parameters
            entry.extend([int(elem) for elem in line[17:]])  # add sound classification parameters as int
            sonochiro_array.append(entry)
    name_of_column = ['filename', 'transect', 'site', 'colour', 'night', 'total_time_sec', 'detector', 'comp_fl',
                      'final_id', 'contact', 'group', 'group_index', 'species', 'species_index',
                      'nb_calls', 'med_freq', 'med_int', 'i_qual', 'i_sc', 'i_buzz']
    return sonochiro_array, name_of_column, skip_dict, excluded_total


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
