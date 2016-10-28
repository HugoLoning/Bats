"""Module for turning a combined imagej output file into a dataset
By Hugo Loning 2016
"""

from sonochiro_dataset_creation import load_transects_array, write_array
import re
import time


def extract_info(filename):
    """Return a list with all relevant info of filename in imagej output context"""
    filename_matcher = re.compile(r'tr([0-9]+)_k([0-9]+)_([0-9][0-9][0-9][0-9])([0-9][0-9])([0-9][0-9])'
                                  r'_[0-9]+_IMG_[0-9]+_(oval|particles)\.csv')
    filename_match = filename_matcher.search(filename)
    return [(elem.isdigit() and [int(elem)] or [elem])[0] for elem in filename_match.group(1, 2, 3, 4, 5, 6)]


def load_imagej_array(imagej_file):
    """Return an array representation of specified imagej combined output csv file"""
    ij_array = []
    with open(imagej_file) as input_file:
        for line in input_file:
            line = line.strip().split(",")
            filename, curr_area = line[0], int(line[1])
            transect, box, year, month, day, area_type = extract_info(filename)
            if box == 75 or box == 78:  # box 75 and 78 are actually 45 and 48
                box -= 30
            ij_array += [[transect, box, year, month, day, curr_area, area_type]]
    return ij_array


def create_imagej_dataset(imagej_file):
    """Return a complete dataset array with total area and area of particles (poo)
    for each bat box measurement in specified imagej combined output csv file.
    """
    ij_array = load_imagej_array(imagej_file)

    # get an entry for each measurement, with a 0 for counting all the poo particles' pixels
    ij_dataset = [row[:-1] + [0] for row in ij_array if row[6] == "oval"]

    # sum all particle areas, all poo, per measurement
    for row in ij_array:
        if row[6] == "particles":
            for entry in range(len(ij_dataset)):
                if row[:5] == ij_dataset[entry][:5]:
                    ij_dataset[entry][6] += row[5]

    # add additional info per measurement
    tr_array = load_transects_array()
    for i in range(len(ij_dataset)):
        transect, box, year, month, day, tot_pix, poo_pix = ij_dataset[i]
        site, colour = tr_array[transect-1][1], tr_array[transect-1][3]
        area_ratio = float(poo_pix) / float(tot_pix)
        ij_dataset[i] = [site, transect, box, colour, year, month, day, poo_pix, tot_pix, area_ratio]
    column_names = ['site', 'transect', 'box', 'colour', 'year', 'month', 'day', 'particle_area',
                    'total_area', 'area_ratio']
    return ij_dataset, column_names


# The script is here
if __name__ == "__main__":
    # Specify input (to load) and output (to write) file
    file_to_load = 'imagej_output_all_with_cleaning.csv'
    file_to_write = 'dataset_imagej_improved.csv'

    # The script
    print("IMAGEJ OUTPUT DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    print("Creating imagej dataset from " + file_to_load + "...\n")
    start_time1 = time.time()  # measure time to complete program
    loaded_array, header_names = create_imagej_dataset(file_to_load)
    print("Loaded in %.3f seconds\n" % (time.time() - start_time1))
    print("Writing imagej dataset to " + file_to_write + "...\n")
    start_time2 = time.time()
    write_array(loaded_array, header_names, file_to_write)
    print("Written in %.3f seconds, total run time %.3f seconds." % (time.time() - start_time2,
                                                                     time.time() - start_time1))
