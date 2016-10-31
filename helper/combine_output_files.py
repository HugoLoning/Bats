"""Contains functions for combining csv output files of sonochiro and imagej for the Light on Nature project."""

import os

from collections import defaultdict
from glob import glob


def combine_sonochiro_files():
    """Return all combined sonochiro output files in directory with this name in a dict of lists with filename as key"""
    csv_files = defaultdict(list)
    for csv_file in glob(r"sonochiro_output_files\*.csv"):
        with open(csv_file, 'r') as sc_file:
            filename = os.path.split(csv_file)[1]
            for line in sc_file:
                csv_files[filename].append(line)
    return dict(csv_files)


def combine_imagej_files():
    """Return all combined csv imagej output files in directory with that name in a list.
    Rows consist of original filename + the value in the area column from imagej.
    """
    csv_files = []
    for csv_file in glob(r"imagej_output_files\*.csv"):
        with open(csv_file, 'r') as ij_file:
            filename = os.path.split(csv_file)[1]
            for line in ij_file:
                if line == ' ,Area,Mean,Min,Max\n':  # if it's a header
                    continue
                area = line.split(",")[1]  # take the area entry
                csv_files.append([filename, area])
    return csv_files
