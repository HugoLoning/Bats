"""This simple script will combine all csv output files into one file.
Headers will not be skipped.
"""

import glob


def combine_all(filename):
    """Combine and write all files of current directory into one csv file with filename as name"""
    with open(filename, 'w') as combined:
        for csv_file in glob.glob('*.csv'):
            if csv_file == filename:
                pass
            else:
                for line in open(csv_file, 'r'):
                    combined.write(line)

# The actual script is here
if __name__ == "__main__":
    combine_all('sonochiro_output_all.csv')
