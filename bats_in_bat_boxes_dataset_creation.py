"""Module for turning dataset from bats in bat boxes into complete datasets.
Be sure to use python3 when running this code. By Hugo Loning 2016
"""

from sonochiro_dataset_creation import load_transects_array, write_array


def load_bats_in_boxes_file(filename):
    """Return bats dataset array of specified file including transect information"""
    tr_array = load_transects_array()
    bats_array = []
    with open(filename) as bats_file:
        for line in bats_file:
            if line.startswith("transect;box"):  # if it's the header
                continue
            # strip and split the line on ; and convert all possible items into int
            line = [(elem.isdigit() and [int(elem)] or [elem])[0] for elem in line.strip().split(';')]
            # convert bat measurements to float
            try:
                line[9], line[10] = float(line[9]), float(line[10])
            except ValueError:  # this will run, unless empty or NA or a case of a value of '>20'
                pass
            # fix box numbering of 75 and 78
            if line[1] == 75 or line[1] == 78:  # box  75 is actually 45, just a new door, same for 78 and 48
                line[1] -= 30
            # remove marked individuals
            if line[-1].startswith('marked'):  # if individual already caught before on that day
                line[6:] = [0, '', '', '', '', '']  # clear the entry
            # add some additional info
            transect = line[0]
            site, colour = tr_array[transect]
            line.insert(0, site)
            line.insert(3, colour)
            bats_array.append(line)
    return bats_array  # [site, transect, box, colour, day, month, year, poo, animals, species, sex, ual, mass, remarks]


def create_data_dict(bats_array):
    """Return a dictionary of specified bats array which counts and scores poo (yes/no) for Pp and bats"""
    data_dict = {}
    for row in bats_array:
        site, transect, box, colour = row[:4]
        poo, nr, species = row[7:10]
        remark = row[-1]
        if transect not in data_dict:  # add it
            data_dict[transect] = [site, transect, colour, 0, 0, 0, 0]  # [site, tr, clr, pp_poo, bat_poo, pp, bats]
        data_dict[transect][4] = data_dict[transect][4] or poo  # update bat_poo
        if not remark.startswith('poo'):  # all remarks starting with poo indicate that the poo is not of Pp
            data_dict[transect][3] = data_dict[transect][3] or poo  # update pp_poo
        data_dict[transect][6] += nr  # update number of bats
        if species == 'pp':
            data_dict[transect][5] += nr  # update number of Pippistrellus pippistrellus
    return data_dict


def create_data_array(bats_array):
    """Return a dataset array with scored poo and counts for Pp and bats in general,
    also return the header names of this dataset array
    """
    data_dict = create_data_dict(bats_array)
    data_array = []
    for tr in data_dict:
        data_array.append(data_dict[tr])
    col_names = ['site', 'transect', 'colour', 'pp_poo', 'bat_poo', 'pp', 'bats']
    return data_array, col_names


def create_body_measurement_array(bats_array):
    """Return a dataset array with body measurements and body condition index for all bats,
    also return the header names of this dataset array
    """
    meas_array = []
    for row in bats_array:
        sex, ual, mass = row[10:13]
        if sex != '':  # if it's a measured bat
            bci_row = row[:-1]  # copy everything but the remark
            try:
                bci_row.append(mass / ual)
            except TypeError:
                bci_row.append('NA')
            del bci_row[7:9]  # remove information of poo and number of animals (always 1)
            meas_array.append(bci_row)
    col_names = ['site', 'transect', 'box', 'colour', 'day', 'month', 'year', 'species', 'sex', 'ual', 'mass', 'bci']
    return meas_array, col_names


def create_sex_counted_array(bats_array):
    """Return a dataset array with counted bats of which sex is known, also return header names"""
    sex_counted_dict = {}
    for row in bats_array:
        site, transect, colour, *rest, species, sex = row[:11]
        if transect not in sex_counted_dict:
            sex_counted_dict[transect] = [transect, site, colour, 0, 0]
        if sex == 'male' and species == 'pp':  # count males
            sex_counted_dict[transect][3] += 1
        elif sex == 'female' and species == 'pp':  # count females
            sex_counted_dict[transect][4] += 1
    sex_counted_array = []
    for value in sex_counted_dict.values():
        transect, site, colour, male, female = value
        sex_counted_array.append([transect, site, colour, 'male', male])
        sex_counted_array.append([transect, site, colour, 'female', female])
    col_names = ['transect', 'site', 'colour', 'sex', 'pp']
    return sex_counted_array, col_names


# Script begins here
if __name__ == "__main__":
    # Specify file to load and files to write
    to_load = 'bats_in_bat_boxes.csv'
    write_bats = 'dataset_bats_in_bat_boxes.csv'
    write_body_measurements = 'dataset_bat_body_measurements.csv'
    write_sex_counted = 'dataset_bats_sex_counted_dataset.csv'

    # The script
    print("BATS IN BAT BOXES DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    loaded = load_bats_in_boxes_file(to_load)
    print("Loaded " + to_load + "...\n")
    array, header_names = create_data_array(loaded)
    write_array(array, header_names, write_bats)
    print("Written bats dataset to " + write_bats + "\n")
    measurement_array, headers = create_body_measurement_array(loaded)
    write_array(measurement_array, headers, write_body_measurements)
    print("Written body measurements dataset to " + write_body_measurements + "\n")
    sex_counted, columns = create_sex_counted_array(loaded)
    write_array(sex_counted, columns, write_sex_counted)
    print("Written sex counted bats dataset to " + write_sex_counted)
