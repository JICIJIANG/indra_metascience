"""
File: build_map.py
Description: Functions to build a nested map for statements.
"""

from collections import defaultdict, Counter

def build_subj_type_obj_year_map(statements):
    data_map = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    for stmt in statements:
        subj_name = stmt.get("subj", {}).get("name")
        rel_type = stmt.get("type")
        obj_name = stmt.get("obj", {}).get("name")
        if not (subj_name and rel_type and obj_name):
            continue

        for ev in stmt.get("evidence", []):
            year = ev.get("year")
            if isinstance(year, int):
                data_map[subj_name][rel_type][obj_name][year] += 1
    return data_map

