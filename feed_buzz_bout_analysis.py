"""Module for analysing feeding buzz bouts"""

import time
from collections import defaultdict

from helper.write_data import write_array
from sonochiro_dataset_creation import load_sonochiro_file


def transect_entries(sonochiro_array):
    """Return a dictionary with for each transect sorted timestamps of all recordings"""
    activity_times = defaultdict(list)
    for row in sonochiro_array:
        transect, sec_time = row[1], row[5]
        activity_times[transect].append(sec_time)
    for tr in activity_times:  # sort all entry times
        activity_times[tr] = sorted(activity_times[tr])
    return activity_times


def find_activity_gaps(sonochiro_array, gap_sec):
    """Return a dictionary with for each transect the end time of each
    activity gap same as or larger than specified gap_sec"""
    activity_gaps = defaultdict(list)
    activity_times = transect_entries(sonochiro_array)
    for transect in activity_times:
        last_activity = 0  # ensure first recording of transect is included
        for activity in activity_times[transect]:
            if activity - last_activity >= gap_sec:  # if it is the end time of a gap longer than gap_sec seconds
                activity_gaps[transect].append(activity)
            last_activity = activity
    return activity_gaps


def find_time_since_end_activity_gap(activity_gap_dict, transect, recording_time):
    """Return time as int since last activity gap for a given transect and recording time"""
    for i, gap_end_time in enumerate(activity_gap_dict[transect]):
        if recording_time < gap_end_time:
            return recording_time - activity_gap_dict[transect][i-1]
        elif recording_time == gap_end_time:
            return 0
    else:  # the entry is after the last gap_end_time so will not be found with above for loop
        return recording_time - activity_gap_dict[transect][-1]


def create_bout_analysis_dataset(sonochiro_array, gap_sec, only_pp=True, buzz_index=2):
    """Create and return a sonochiro array with additional information per file on time since last gap
    and whether a buzz index was higher or the same as specified buzz_index. Can filter out everything
    that is not identified as a Pippistrellus pippistrellus.
    """
    if only_pp:  # filter out entries other than Pippistrellus pippistrellus
        edited_array = [row for row in sonochiro_array if row[8] == "PippiT"]
    else:
        edited_array = sonochiro_array[:]  # create copy to avoid editing original array
    activity_gaps = find_activity_gaps(edited_array, gap_sec)
    for i, row in enumerate(edited_array):
        transect, time_in_sec = row[1], row[5]
        gap_dt = find_time_since_end_activity_gap(activity_gaps, transect, time_in_sec)
        row.extend([gap_dt, 0])
        if row[19] >= buzz_index:
            row[-1] = 1
        edited_array[i] = row
    column_names = ['filename', 'transect', 'site', 'colour', 'night', 'total_time_sec', 'detector', 'comp_fl',
                    'final_id', 'contact', 'group', 'group_index', 'species', 'species_index',
                    'nb_calls', 'med_freq', 'med_int', 'i_qual', 'i_sc', 'i_buzz', 'gap_dt', 'buzz']
    return edited_array, column_names


if __name__ == "__main__":
    gap = 30  # which amount of seconds is defined as a gap
    file_to_write = "dataset_bout_analysis_with_{}_second_gaps.csv".format(gap)

    start = time.time()
    sc = load_sonochiro_file()[0]
    print("loaded sc file in {:.3f} seconds".format(time.time()-start))
    start2 = time.time()
    bout_array, col_names = create_bout_analysis_dataset(sc, gap)
    print("created bout array in {:.3f} seconds".format(time.time() - start2))
    write_array(bout_array, col_names, file_to_write)
