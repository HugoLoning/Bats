"""This simple script will combine all imagej output files into one file.
Headers will be skipped.
"""

import glob


def combine_all_imagej(filename):
    """Combine and write all csv imagej output files of current directory into one csv file with filename as name.
    Rows consist of original filename + the value in the area column from imagej.
    """
    with open(filename, 'w') as combined:
        for csv_file in glob.glob('*.csv'):
            if csv_file == filename:
                pass
            else:
                for line in open(csv_file, 'r'):
                    if line == ' ,Area,Mean,Min,Max\n':  # if it's a header
                        continue
                    area = line.split(",")[1]  # take the area entry
                    combined.write(csv_file + "," + area + "\n")

# The actual script is here
if __name__ == "__main__":
    combine_all_imagej('imagej_output_all.csv')
