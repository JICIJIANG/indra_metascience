"""
File: find_peak.py
Description: Functions to determine peak years and detect decline.
"""

def find_peak_and_decline(counts_by_year):
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

