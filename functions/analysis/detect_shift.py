"""
File: detect_shift.py
Description: Functions for detecting interest shifts in research trends.
"""


from .find_peak import find_peak_and_decline

def detect_interest_shift(data_map, current_subj, current_type, current_obj):
    counts_obj1 = data_map[current_subj][current_type][current_obj]
    peak_year_1, is_decline_1 = find_peak_and_decline(counts_obj1)

    if not peak_year_1 or not is_decline_1:
        return []

    shift_objs = []
    for obj2, counts_obj2 in data_map[current_subj][current_type].items():
        if obj2 == current_obj:
            continue
        peak_year_2, _ = find_peak_and_decline(counts_obj2)
        if peak_year_2 and peak_year_2 > peak_year_1:
            shift_objs.append(obj2)
    return shift_objs
