"""
File: analyze_trends.py
Description: Functions for analyzing trends, conflicts, and interest shifts.
"""

from collections import Counter
from functions.analysis.build_map import build_subj_type_obj_year_map
from functions.analysis.detect_shift import detect_interest_shift
from functions.analysis.find_peak import find_peak_and_decline
from functions.ioutils import export_correct_info
from functions.ioutils import export_yearly_counts_to_tsv



def analyze_trends_and_construct_summary(statements_correct, all_data, output_dir):
    """
    1) Calculate yearly publication counts for correctness=1 evidence
    2) Detect conflicts (subj=obj, type != current_type)
    3) Detect interest shift
    4) Return text summary
    """
    if not statements_correct:
        return "No statements provided for trend analysis.\n"

    current_subj = statements_correct[0].get("subj", {}).get("name", "UnknownSubj")
    current_obj = statements_correct[0].get("obj", {}).get("name", "UnknownObj")
    current_type = statements_correct[0].get("type", "UnknownType")

    # 5.1: Count correctness=1 evidence by year
    counts_by_year = Counter()
    for stmt in statements_correct:
        for ev in stmt.get("evidence", []):
            year = ev.get("year")
            if isinstance(year, int):
                counts_by_year[year] += 1

    if not counts_by_year:
        return "No correct evidence available for trend analysis.\n"

    export_yearly_counts_to_tsv(counts_by_year, output_dir, current_type, current_subj, current_obj)

    peak_year = max(counts_by_year, key=lambda y: counts_by_year[y])
    peak_count = counts_by_year[peak_year]
    min_year = min(counts_by_year, key=lambda y: counts_by_year[y])
    min_count = counts_by_year[min_year]

    sorted_years = sorted(counts_by_year.keys())
    trend_desc = [f"Year {y}: {counts_by_year[y]} publication(s)" for y in sorted_years]
    trend_summary = (
        "Publication trend (correctness=1 evidence):\n"
        + "\n".join(trend_desc)
        + f"\n\nPeak publication year: {peak_year} ({peak_count} publications).\n"
        + f"Lowest publication year: {min_year} ({min_count} publications).\n"
    )

    # 5.2: Conflicts
    conflicting_stmts = []
    for stmt in statements_correct:
        if (stmt.get("subj", {}).get("name") == current_subj
            and stmt.get("obj", {}).get("name") == current_obj
            and stmt.get("type") != current_type):
            conflicting_stmts.append(stmt)

    if not conflicting_stmts:
        conflict_summary = "No conflicting statements found.\n"
    else:
        conflict_type_years = {}
        for cstmt in conflicting_stmts:
            ctype = cstmt.get("type", "UnknownType")
            for ev in cstmt.get("evidence", []):
                if ev.get("correctness", 0) == 1:
                    year = ev.get("year")
                    if isinstance(year, int):
                        conflict_type_years.setdefault(ctype, []).append(year)

        conflict_types_counter = Counter(st.get("type") for st in conflicting_stmts)
        conflict_desc_list = []
        for ctype, cnt in conflict_types_counter.items():
            years_list = conflict_type_years.get(ctype, [])
            if years_list:
                first_appearance = min(years_list)
                last_appearance = max(years_list)
                conflict_desc_list.append(
                    f"{ctype} ({cnt} statements) from ~{first_appearance} to ~{last_appearance}"
                )
            else:
                conflict_desc_list.append(f"{ctype} ({cnt} statements) - no correctness=1 evidence found")

        conflict_desc = "; ".join(conflict_desc_list)
        conflict_summary = (
            f"Conflicts for (subj={current_subj}, obj={current_obj}):\n"
            f"{conflict_desc}\n"
        )

    # 5.3: Interest shift
    data_map = build_subj_type_obj_year_map(statements_correct)
    shift_objs = detect_interest_shift(data_map, current_subj, current_type, current_obj)
    if shift_objs:
        max_show = 5
        top_objs = shift_objs[:max_show]
        if len(shift_objs) > max_show:
            remainder = len(shift_objs) - max_show
            shift_desc = ", ".join(top_objs) + f", and {remainder} more"
        else:
            shift_desc = ", ".join(top_objs)
        shift_summary = (
            f"Potential interest shift: after the peak, there is an increase in: {shift_desc}.\n"
        )
    else:
        shift_summary = "No clear indication of interest shift.\n"

    return (
        "\n=== Trend & Conflicts (correctness=1) ===\n"
        + trend_summary
        + conflict_summary
        + shift_summary
        + "\n================================================\n"
    )

