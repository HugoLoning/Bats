"""Module for turning a combined imagej output file into a dataset.
By Hugo Loning 2016
"""

import re
import time

from helper.combine_output_files import combine_imagej_files
from helper.load_info import load_transects
from helper.write_data import write_array


def extract_info(filename):
    """Return a list with all relevant info of filename in imagej output context"""
    match = re.search(r'tr(\d+)_k(\d+)_(\d{4})(\d{2})(\d{2})_\d+_IMG_\d+_(oval|particles)\.csv', filename)
    return [int(elem) if elem.isdigit() else elem for elem in match.groups()]


def load_imagej_array():
    """Return an array representation with filename extracted info of combined imagej output"""
    loaded_array = combine_imagej_files()
    ij_array = []
    for line in loaded_array:
        filename, curr_area = line
        transect, box, year, month, day, area_type = extract_info(filename)
        if box == 75 or box == 78:  # box 75 and 78 are actually 45 and 48
            box -= 30
        ij_array.append([transect, box, year, month, day, int(curr_area), area_type])
    return ij_array


def create_imagej_dataset():
    """Return a complete dataset array with total area and area of particles (poo)
    for each bat box measurement in imagej output files.
    """
    ij_array = load_imagej_array()

    # get an entry for each measurement, with a 0 for counting all the poo particles' pixels
    ij_dataset = [row[:-1] + [0] for row in ij_array if row[6] == "oval"]

    # sum all particle areas, all poo, per measurement
    for row in ij_array:
        if row[6] == "particles":
            for index, entry in enumerate(ij_dataset):
                if row[:5] == entry[:5]:  # if it's the same measurement
                    ij_dataset[index][6] += row[5]

    # add additional info per measurement
    tr_array = load_transects()
    final_ij_dataset = []
    for row in ij_dataset:
        transect, box, year, month, day, tot_pix, poo_pix = row
        site, colour = tr_array[transect]
        area_ratio = poo_pix / tot_pix
        final_ij_dataset.append([site, transect, box, colour, year, month, day, poo_pix, tot_pix, area_ratio])
    column_names = ['site', 'transect', 'box', 'colour', 'year', 'month', 'day', 'particle_area',
                    'total_area', 'area_ratio']
    return final_ij_dataset, column_names


# The script is here
if __name__ == "__main__":
    # Specify output file
    file_to_write = 'dataset_imagej.csv'

    # The script
    print("IMAGEJ OUTPUT DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    print("Creating imagej dataset from output files...\n")
    start_time1 = time.time()  # measure time to complete program
    loaded, header_names = create_imagej_dataset()
    print("Loaded in {:.3f} seconds\n".format(time.time() - start_time1))
    print("Writing imagej dataset to {}...\n".format(file_to_write))
    start_time2 = time.time()
    write_array(loaded, header_names, file_to_write)
    print("Written in {:.3f} seconds, total run time {:.3f} seconds.".format(time.time() - start_time2,
                                                                             time.time() - start_time1))
