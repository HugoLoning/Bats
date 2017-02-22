"""Module for turning dataset from all bat box checks 2012-2016 into complete datasets.
Be sure to use python3 when running this code. By Hugo Loning 2016
"""

from helper.load_info import load_transects
from helper.write_data import write_array


def load_bats_in_boxes_file(filename):
    """Return bats dataset array of specified file including transect information"""
    tr_array = load_transects()
    bats_array = []
    with open(filename) as bats_file:
        for line in bats_file:
            if line.startswith("transect;box"):  # if it's the header
                continue
            # strip and split the line on ; and convert all possible items into int
            line = [int(elem) if elem.isdigit() else elem for elem in line.strip().split(';')]
            # convert bat measurements to float
            try:
                line[11], line[12] = float(line[11]), float(line[12])
            except ValueError:  # this will run, unless empty or NA or a case of a value of '>20'
                pass
            # fix box numbering of 75 and 78
            if line[1] in (75, 78):  # box  75 is actually 45, just a new door, same for 78 and 48
                line[1] -= 30
            # remove marked individuals
            if line[-1].startswith('marked'):  # if individual already caught before on that day
                line[6:13] = [0, 0, 0, '', '', '', '']  # clear the entry
            line.insert(8, 0)
            if line[10] == "pp":  # if species is Pippistrellus pippistrellus
                line[8] += line[9]  # add the nr of bats to the nr of pp
            # add some additional info
            site, colour = tr_array[line[0]]
            line.insert(0, site)
            line.insert(3, colour)
            bats_array.append(line)
    return bats_array  # [site, transect, box, colour, day, month, year, round, pp_presence,
    #                     presence, bats, pp, species, sex, ual, mass, observer, remarks]


def create_all_year_data(bats_array):
    """Return array of all measurements in 2012-2016 with one entry per bat box check, summing up all found
    bats and pp per check, discarding measurement data.
    """
    observations = {}
    for row in bats_array:
        box_yr_obs = tuple([row[2]] + row[6:8])  # create entry for every combination of box, year, round observed
        if box_yr_obs not in observations:  # create new entry
            observations[box_yr_obs] = row[:12] + [row[16]]
        else:  # update entry
            observations[box_yr_obs][8] = row[8] or observations[box_yr_obs][8]  # update presence of pp
            observations[box_yr_obs][9] = row[9] or observations[box_yr_obs][9]  # update presence of bats
            observations[box_yr_obs][10] += row[10]  # update nr of pp
            observations[box_yr_obs][11] += row[11]  # update nr of bats
            if observations[box_yr_obs][12] == "":  # if there is no observer, take last remark
                observations[box_yr_obs][12] = row[12]
    dataset = []
    for entry in observations:
        dataset.append(observations[entry])
    header = ['site', 'transect', 'box', 'colour', 'day', 'month', 'year', 'round',
              'pp_presence', 'presence', 'pp', 'bats', 'observer']
    return dataset, header


def create_sex_counted_array(bats_array):
    """Return a dataset array with counted bats of which sex is known, also return header names"""
    sex_counted_dict = {}
    for row in [line for line in bats_array if line[6] == 2016]:
        site, transect, colour, species, sex = row[0], row[1], row[3], row[12], row[13]
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
    to_load = 'all_bat_box_checks_2012_to_2016.csv'
    write_bats = 'dataset_bat_box_checks_2012_to_2016.csv'
    write_sex_counted = 'dataset_sex_counted_bats_2016.csv'

    # The script
    print("BATS IN BAT BOXES DATA CREATION SCRIPT FOR LON BY HUGO LONING 2016\n")
    loaded = load_bats_in_boxes_file(to_load)
    print("Loaded {}...\n".format(to_load))
    array, header_names = create_all_year_data(loaded)
    write_array(array, header_names, write_bats)
    print("Written bats dataset to {}\n".format(write_bats))
    sc_array, sc_header = create_sex_counted_array(loaded)
    write_array(sc_array, sc_header, write_sex_counted)
    print("Written sex counted dataset to {}".format(write_sex_counted))
