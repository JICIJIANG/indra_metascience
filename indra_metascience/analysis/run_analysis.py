# indra_metascience/scripts/run_analysis.py

import os
import json
from indra_metascience.util.correctness_checker import (
    assess_and_filter_correctness,
    export_correct_info
)
from indra_metascience.util.trend_analysis import analyze_trends_and_conflicts
from indra_metascience.util.story_generator import generate_story_from_statements

def save_updated_json(json_path, data):
    """
    Saves the full data (with correctness=0/1 labels) back to a JSON file and creates a backup of the old file.
    """
    backup_path = json_path + ".bak"
    if os.path.exists(json_path):
        os.rename(json_path, backup_path)
        print(f"[INFO] A backup of the old JSON file is created: {backup_path}")
    else:
        print("[WARN] Original JSON file does not exist, cannot create a backup.")

    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Updated JSON saved to: {json_path}")


def main():
    # 1) Load statements from JSON
    script_dir = os.path.dirname(__file__)
    input_file = os.path.join(script_dir, '..', 'resources', 'cdk12_statements.json')
    input_file = os.path.abspath(input_file)

    with open(input_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    # 2) Ask user for type, subj, and obj
    selected_type = input("Please enter Statement type (e.g. Activation): ").strip()
    selected_subj = input("Please enter subj entity (e.g. TNF): ").strip()
    selected_obj = input("Please enter obj entity (e.g. IL10): ").strip()

    # 3) Partition into target vs. conflict (comparing type for the same subj/obj)
    target_statements = []
    conflicting_statements = []
    for stmt in all_data:
        subj_name = stmt.get("subj", {}).get("name", "")
        obj_name = stmt.get("obj", {}).get("name", "")
        rtype = stmt.get("type", "")
        if subj_name == selected_subj and obj_name == selected_obj:
            if rtype == selected_type:
                target_statements.append(stmt)
            else:
                conflicting_statements.append(stmt)

    # Print basic info
    print(f"[INFO] Found {len(target_statements)} target statements, {len(conflicting_statements)} conflicting statements.")

    # 4) Check correctness on both target and conflict statements
    #    Then extract correctness=1 statements
    _, pruned_target_statements = assess_and_filter_correctness(target_statements)
    _, pruned_conflict_statements = assess_and_filter_correctness(conflicting_statements)

    output_dir = "./results"
    os.makedirs(output_dir, exist_ok=True)

    # 5) Export correctness=1 target statements to a separate JSON file
    correct_info_path = os.path.join(output_dir, f"correct_{selected_subj}_{selected_obj}_{selected_type}.json")
    export_correct_info(pruned_target_statements, correct_info_path)

    # 5.1)Export correctness=1 conflict statements
    if pruned_conflict_statements:
        conflict_info_path = os.path.join(output_dir, f"conflict_correct_{selected_subj}_{selected_obj}_{selected_type}.json")
        export_correct_info(pruned_conflict_statements, conflict_info_path)
        print(f"[INFO] correctness=1 conflict statements exported to: {conflict_info_path}")
    else:
        print("[INFO] No correctness=1 conflict statements found.")

    # ============= Combine target+conflict for a unified story ==============
    all_correct_statements = pruned_target_statements + pruned_conflict_statements

    if all_correct_statements:
        # If you want a combined analysis/trend summary for both target and conflict:
        trend_conflict_summary_all = analyze_trends_and_conflicts(all_correct_statements, output_dir)
        print("\n=== Combined Trend & Conflict Analysis ===")
        print(trend_conflict_summary_all)

        # 6) Generate a story based on combined statements
        print("\n=== Generating a unified story from target + conflict statements ===")
        story_text = generate_story_from_statements(all_correct_statements, trend_conflict_summary_all)
        print("\n=== Final Story (Unified) ===")
        print(story_text)
    else:
        print("[INFO] No correctness=1 statements at all (target + conflict). Skipping story generation.")

    # 7) Save updated JSON (with correctness=0/1 labels)
    save_updated_json(input_file, all_data)

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
