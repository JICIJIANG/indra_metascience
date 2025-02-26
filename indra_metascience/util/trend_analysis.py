# indra_metascience/util/trend_analysis.py

import os
from collections import defaultdict, Counter

def build_subj_type_obj_year_map(statements):
    """
    Build a nested dictionary structure: (subj, type, obj) -> year -> count
    Only considers evidence with correctness=1.
    """
    from collections import Counter
    data_map = defaultdict(lambda: defaultdict(lambda: defaultdict(Counter)))
    for stmt in statements:
        subj_name = stmt.get("subj", {}).get("name")
        rel_type = stmt.get("type")
        obj_name = stmt.get("obj", {}).get("name")
        if not (subj_name and rel_type and obj_name):
            continue

        for ev in stmt.get("evidence", []):
            # Only count correctness=1 evidence
            if ev.get("correctness", 0) == 1:
                year = ev.get("year")
                if isinstance(year, int):
                    data_map[subj_name][rel_type][obj_name][year] += 1
    return data_map

def find_peak_and_decline(counts_by_year):
    """
    Find the peak year (the one with the highest publication count)
    and check whether there's a post-peak decline (average after the peak
    is less than 50% of peak).
    Returns (peak_year, is_decline).
    """
    if not counts_by_year:
        return None, False
    
    sorted_years = sorted(counts_by_year.keys())
    peak_year = max(counts_by_year, key=lambda y: counts_by_year[y])
    peak_val = counts_by_year[peak_year]
    years_after_peak = [y for y in sorted_years if y > peak_year]
    if not years_after_peak:
        return peak_year, False

    avg_after = sum(counts_by_year[y] for y in years_after_peak) / len(years_after_peak)
    is_decline = (avg_after < peak_val * 0.5)
    return peak_year, is_decline

def detect_interest_shift(data_map, current_subj, current_type, current_obj):
    """
    If (subj, type, obj) shows a decline after its peak, check if there's a (subj, type, obj2)
    whose peak year is later than obj1's peak year.
    """
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

def export_yearly_counts_to_tsv(counts_by_year, output_dir, selected_type, selected_subj, selected_obj):
    """
    Export {year: count} to a TSV file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{selected_type}_{selected_subj}_{selected_obj}_yearly_counts.tsv"
    tsv_path = os.path.join(output_dir, filename)

    with open(tsv_path, 'w', encoding='utf-8') as f:
        f.write("year\tcount\n")
        for y in sorted(counts_by_year.keys()):
            f.write(f"{y}\t{counts_by_year[y]}\n")
    print(f"[INFO] TSV file exported to: {tsv_path}")

def analyze_trends_and_conflicts(statements_correct, output_dir):
    """
    Perform trend analysis (yearly stats, peak, min, etc.) for correctness=1 statements.
    Check conflicts (same subj/obj but different type, also requiring correctness=1).
    Detect potential interest shift based on post-peak decline.
    Return a text summary.
    """

    if not statements_correct:
        return "No statements provided for trend analysis.\n"

    # Use the first statement to identify current subj/obj/type
    current_subj = statements_correct[0].get("subj", {}).get("name", "UnknownSubj")
    current_obj = statements_correct[0].get("obj", {}).get("name", "UnknownObj")
    current_type = statements_correct[0].get("type", "UnknownType")

    # 1) Count correctness=1 evidence by year
    from collections import Counter
    counts_by_year = Counter()
    for stmt in statements_correct:
        for ev in stmt.get("evidence", []):
            if ev.get("correctness", 0) == 1:
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
    trend_lines = [f"Year {y}: {counts_by_year[y]}" for y in sorted_years]
    trend_summary = (
        "Publication trend (correctness=1 evidence):\n"
        + "\n".join(trend_lines)
        + f"\nPeak year: {peak_year} ({peak_count} pubs)"
        + f"\nLowest year: {min_year} ({min_count} pubs)\n"
    )

    # 2) Detect conflicts (within the same subj/obj but a different type),
    #    ensuring the conflicting statement also has correctness=1 evidence.
    conflicting_stmts = []
    for stmt in statements_correct:
        if (stmt.get("subj", {}).get("name") == current_subj
            and stmt.get("obj", {}).get("name") == current_obj
            and stmt.get("type") != current_type
            and any(ev.get("correctness", 0) == 1 for ev in stmt.get("evidence", []))
        ):
            conflicting_stmts.append(stmt)

    if not conflicting_stmts:
        conflict_summary = "No conflicting statements found.\n"
    else:
        conflict_summary_list = []
        ctype_counter = Counter(st.get("type") for st in conflicting_stmts)
        for ctype, cnt in ctype_counter.items():
            conflict_summary_list.append(f"{ctype} ({cnt} statements)")
        conflict_summary = "Other types found: " + "; ".join(conflict_summary_list) + "\n"

    # 3) Detect interest shift
    data_map = build_subj_type_obj_year_map(statements_correct)
    shift_objs = detect_interest_shift(data_map, current_subj, current_type, current_obj)
    if shift_objs:
        top_objs = shift_objs[:5]
        tail_count = len(shift_objs) - len(top_objs)
        if tail_count > 0:
            shift_objs_str = ", ".join(top_objs) + f"...(+{tail_count} more)"
        else:
            shift_objs_str = ", ".join(top_objs)
        shift_summary = f"Potential interest shift to: {shift_objs_str}\n"
    else:
        shift_summary = "No clear indication of interest shift.\n"

    return (
        "\n=== Trend & Conflicts (correctness=1) ===\n"
        + "\n##trend summary: \n"
        + trend_summary
        + "\n##conflict summary: \n"
        + conflict_summary
        + "\n##interest shift: \n"
        + shift_summary
        + "\n==========================================\n"
    )
