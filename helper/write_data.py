"""Module for writing csv files with specified header names"""


def write_array(array, header_names, output_file):
    """Write a two-dimensional array with header made from header_names to a specified csv file"""
    with open(output_file, "w") as output:
        output.write(",".join(header_names) + "\n")  # write header
        for row in array:
            output.write(",".join([str(element) for element in row]) + "\n")  # write rows
