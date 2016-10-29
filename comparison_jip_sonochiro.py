"""File for comparing Jip's feeding buzz data with sonochiro Ibuz values.
By Hugo Loning 2016
"""

from sonochiro_dataset_creation import convert_to_sec, load_sun_data_array, lookup_sun_data_array, write_array
from collections import defaultdict
import time

# The functions


def array_from_input(jip_sc_file):
    """Create dataset from input file, return list"""
    array = []
    with open(jip_sc_file) as input_file:
        for line in input_file:
            if line.startswith("File;"):  # if it's the header
                continue
            line = line.strip().split(";")
            line = [(elem.isdigit() and [int(elem)] or [elem])[0] for elem in line]  # convert to int if possible
            year, month, day, hour, minute, second = line[2:8]
            line[2:8] = [convert_to_sec(year, month, day, hour, minute, second)]  # replace ymdhms by total in sec's
            array += [line]
    return array


def find_min_max_per_transect(jip_sc_array):
    """Return a dict with per transect the minimum and maximum 'total_time_sec' in the format transect:[min:max]
    based on supplied array of combined_jip_sc.
    """
    min_max_dict = {}
    for row in jip_sc_array:
        transect, total_time = row[1:3]
        if transect not in min_max_dict:
            min_max_dict[transect] = [total_time, total_time]
        if total_time < min_max_dict[transect][0]:
            min_max_dict[transect][0] = total_time
        elif total_time > min_max_dict[transect][1]:
            min_max_dict[transect][1] = total_time
    return min_max_dict


def find_num_of_entries_per_transect(jip_sc_array, sec_per_unit):
    """Return a dict with per transect the start time in total seconds and the number of entries
    needed for creating an empty array to hold all units for unit length sec_per_unit based on
    supplied combined_jip_sc.
    """
    num_of_entries_dict = {}
    mm_dict = find_min_max_per_transect(jip_sc_array)
    for transect in mm_dict:
        start_time_offset = mm_dict[transect][0] % sec_per_unit
        start_time = mm_dict[transect][0] - start_time_offset
        total_time = mm_dict[transect][1] - start_time
        total_entries_needed = total_time // sec_per_unit + 1
        num_of_entries_dict[transect] = [start_time, total_entries_needed]
    return num_of_entries_dict


def create_empty_comparison_dict(jip_sc_array, sec_per_unit):
    """Create arrays in a dict with transect as key with the right amount of empty entries for each transect
    of supplied jip_sc_array, taking into account the seconds per unit. Return this dictionary.
    """
    entry_dict = find_num_of_entries_per_transect(jip_sc_array, sec_per_unit)
    sun_data = load_sun_data_array()
    empty_dict = defaultdict(list)
    for transect in entry_dict:
        start_time = entry_dict[transect][0]
        entries_needed = entry_dict[transect][1]
        for entry_num in range(entries_needed):
            curr_time = start_time + entry_num * sec_per_unit
            night = lookup_sun_data_array(sun_data, curr_time)
            empty_dict[transect].append([transect, night, curr_time, 0, 0, 0, 0])
    return empty_dict


def create_comparison_dict(jip_sc_array, min_per_unit, buzz_index):
    """Take a jip_sc_array, and return a dict with transect as key with for each transect per time unit
    the number of times Jip scored a buzz; the total of all ibuzzes encountered added; a count of all files
    which have a buzz index higher than zero and a count of all files which have a buzz index higher than
    specified buzz_index.
    """
    sec_per_unit = min_per_unit * 60
    comparison_dict = create_empty_comparison_dict(jip_sc_array, sec_per_unit)
    entries_dict = find_num_of_entries_per_transect(jip_sc_array, sec_per_unit)
    for row in jip_sc_array:
        transect, total_time = row[1:3]
        start_time = entries_dict[transect][0]
        time_index = (total_time - start_time) // sec_per_unit
        if row[5] == 1:  # if Jip scored a buzz
            comparison_dict[transect][time_index][3] += 1
        comparison_dict[transect][time_index][4] += row[4]  # add all ibuzzes
        if row[4] > 0:  # if there is a feeding buzz index higher than 0
            comparison_dict[transect][time_index][5] += 1
        if row[4] >= buzz_index:  # if feeding buzz index is higher than threshold
            comparison_dict[transect][time_index][6] += 1  # count file with sufficient buzz index
    return comparison_dict


def create_comparison_array(jip_sc_array, min_per_unit, buzz_index, filter_empty_entries=True):
    """Create an array with for each transect per specified time unit the number of times Jip scored a buzz; the
    total of all ibuzzes encountered added; a count of all files which have a buzz index higher than zero and a
    count of all files which have a buzz index higher than specified buzz_index. Can filter out empty entries.
    Return a tuple of length 2 with the array and a list of header names.
    """
    comparison_dict = create_comparison_dict(jip_sc_array, min_per_unit, buzz_index)
    comparison_array = []
    for array in comparison_dict.values():
        comparison_array.extend(array)
    if filter_empty_entries:
        comparison_array = [entry for entry in comparison_array if sum(entry[3:]) > 0]
    column_names = ['transect', 'night', 'time_in_sec', 'buzz_count', 'ibuz_total', 'ibuz_count', 'ibuz_count_thresh']
    return comparison_array, column_names


# The script is here
if __name__ == "__main__":
    minutes_unit = 30  # set minute interval in which to compare
    ibuz_th = 2  # set ibuz threshold under which entries will be excluded

    # Specify input (to load) and output (to write) file
    file_to_load = "combined_jip_sc.csv"
    file_to_write = "dataset_jip_sc_per_%d_min_with_ibuz_threshold_of_%d.csv" % (minutes_unit, ibuz_th)

    # The script
    print("SONOCHIRO AND JIP COMPARISON DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    print("Loading " + file_to_load + "...\n")
    start_time1 = time.time()  # measure time to complete program
    loaded_array = array_from_input(file_to_load)
    print("Loaded in %.3f seconds\n" % (time.time() - start_time1))
    print("Creating comparison array...\n")
    start_time2 = time.time()
    fb_arr, names = create_comparison_array(loaded_array, minutes_unit, ibuz_th)
    print("Created in %.3f seconds.\n" % (time.time()-start_time2))
    print("Writing feeding buzz array to " + file_to_write + "...\n")
    start_time3 = time.time()
    write_array(fb_arr, names, file_to_write)
    print("Written in %.3f seconds, total run time %.1f seconds." % (time.time() - start_time3,
                                                                     time.time() - start_time1))
