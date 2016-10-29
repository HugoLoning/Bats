"""Module for creating a feeding buzz dataset from sonochiro output file for the Light on Nature project.
Be sure to use python3 when running this code. By Hugo Loning 2016
"""

from sonochiro_dataset_creation import load_sonochiro_file, load_transects_array, write_array
from collections import defaultdict
import time


def filter_sonochiro_array(sonochiro_array, filter_id="PippiT"):
    """Return the sonochiro_array as array with only entries where 'final_id' is filter_id"""
    filtered_sonochiro_array = [row for row in sonochiro_array if row[8] == filter_id]
    return filtered_sonochiro_array


def find_nights_per_site(sonochiro_array):
    """Return a dict with per site a list of all nights"""
    nights = defaultdict(list)  # create an empty list for each key (site) to contain all the nights
    for row in sonochiro_array:
        site, night = row[2], row[4]
        if night not in nights[site]:
            nights[site].append(night)
    return nights


def create_empty_fb_dict(nights_dict):
    """Return a dict with per transect an entry for each night, total and feeding buzz initialised at 0"""
    tr_array = load_transects_array()
    fb_dict = defaultdict(list)
    for row in tr_array:
        transect, site, *rest, colour = row[:4]
        for night in nights_dict[site]:
            fb_dict[transect].append([site, transect, colour, night, 0, 0])
    return fb_dict


def lookup_night_index(nights_dict, site, night):
    """Return the index as int of given night corresponding to given site in the nights list of nights_dict"""
    for index, current_night in enumerate(nights_dict[site]):
        if current_night == night:
            return index


def create_fb_dict(sonochiro_array, buzz_index):
    """Return a dict with per transect per night the number of files and the number of files with a feeding buzz
    the same or higher as specified buzz_index.
    """
    nights_dict = find_nights_per_site(sonochiro_array)
    fb_dict = create_empty_fb_dict(nights_dict)
    for row in sonochiro_array:
        transect, site, night, ibuz = row[1], row[2], row[4], row[19]
        night_index = lookup_night_index(nights_dict, site, night)
        fb_dict[transect][night_index][4] += 1  # count file
        if ibuz >= buzz_index:  # if buzz index is high enough
            fb_dict[transect][night_index][5] += 1  # count feeding buzz
    return fb_dict


def create_feeding_buzz_array(sonochiro_array, buzz_index=2):
    """Return an array and a list of corresponding header names with an entry per transect per night with
    counts of the number of files and the number of files with a feeding buzz index the same or higher as
    specified buzz_index.
    """
    fb_dict = create_fb_dict(sonochiro_array, buzz_index)
    fb_array = []
    for array in fb_dict.values():
        fb_array.extend(array)
    column_names = ['site', 'transect', 'colour', 'night', 'total', 'feed_buzz']
    return fb_array, column_names


# The actual script is here
if __name__ == "__main__":
    # Specify input (to load) and output (to write) file
    file_to_load = "sonochiro_output_all.csv"
    file_to_write = "dataset_sonochiro_feeding_buzz.csv"

    # The script
    print("SONOCHIRO FEEDING BUZZ DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    print("Loading " + file_to_load + "...\n")
    start_time1 = time.time()  # measure time to complete program
    sc, cn, skipped, excluded = load_sonochiro_file(file_to_load)  # cn will not be used
    print("Loaded in %.3f seconds, of %d total entries, %d entries were unusable\n"
          "and skipped, %d entries were in nights that did not have all detectors\n"
          "running and were excluded.\n" % (time.time() - start_time1, len(sc) + len(skipped) + excluded,
                                            len(skipped), excluded))
    print("Filtering out all but common pippistrelle entries...\n")
    start_time2 = time.time()
    filtered = filter_sonochiro_array(sc)
    print("Filtered in %.3f seconds, %d entries were filtered out.\n" % (time.time()-start_time2,
                                                                         len(sc)-len(filtered)))
    print("Creating feeding buzz array...\n")
    start_time3 = time.time()
    fb_arr, names = create_feeding_buzz_array(filtered)
    print("Created in %.3f seconds.\n" % (time.time() - start_time3))
    print("Writing feeding buzz array to " + file_to_write + "...\n")
    start_time4 = time.time()
    write_array(fb_arr, names, file_to_write)
    print("Written in %.3f seconds, total run time %.1f seconds, type \'skipped\' for \n"
          "a dictionary (line:filename) of the entries skipped during file loading." % (time.time() - start_time4,
                                                                                        time.time() - start_time1))
