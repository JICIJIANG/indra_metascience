import json
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

from functions.openai_utils import assess_evidence_vs_statement, construct_input_for_openai, generate_story_with_openai
from functions.ioutils import save_updated_json, export_correct_info
from functions.analysis.analyze_trends import analyze_trends_and_construct_summary
from functions.analysis.build_map import build_subj_type_obj_year_map
from functions.analysis.detect_shift import detect_interest_shift
from functions.analysis.find_peak import find_peak_and_decline
from collections import defaultdict, Counter
from functions.ioutils import export_yearly_counts_to_tsv
import openai


# ============================
# Main entry
# ============================
def main():
    """
    Steps:
    1) Load JSON
    2) Ask user for (type, subj, obj)
    3) Split into target statements and conflicting statements
    4) Evaluate correctness using OpenAI
    5) Filter out incorrect evidence
    6) Analyze trends & conflicts (only correctness=1)
    7) Export correctness=1 data to a separate JSON
    8) Construct prompt and generate the final story with OpenAI
    9) Save updated JSON
    """
    input_file = "./resources/cdk12_statements.json"
    output_dir = "./results"
    os.makedirs(output_dir, exist_ok=True)

    # 1) Load all data
    with open(input_file, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    # 2) User input
    selected_type = input("Please enter Statement type (e.g. Activation/Inhibition): ").strip()
    selected_subj = input("Please enter subj entity (e.g. CDK12): ").strip()
    selected_obj = input("Please enter obj entity (e.g. BRCA1): ").strip()

    # 3) Partition into target vs conflict
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

    if not target_statements:
        print(f"[WARN] No target statements found for (type={selected_type}, subj={selected_subj}, obj={selected_obj}).")
    else:
        print(f"[INFO] Found {len(target_statements)} target statements.")

    if conflicting_statements:
        print(f"[INFO] Found {len(conflicting_statements)} conflicting statements with different types.")

    # 4) Evaluate correctness
    for stmt in target_statements:
        assess_evidence_vs_statement(stmt)
    for stmt in conflicting_statements:
        assess_evidence_vs_statement(stmt)

    # 5) Filter target statements => correctness=1 only
    pruned_target_statements = filter_incorrect_evidence(target_statements)
    print(f"[INFO] pruned_target_statements: {len(pruned_target_statements)} statements remain with correctness=1 evidence.")

    # 6) Trend & conflict analysis for pruned statements
    if pruned_target_statements:
        trend_conflict_summary = analyze_trends_and_construct_summary(
            pruned_target_statements,
            all_data,
            output_dir
        )
        print(trend_conflict_summary)
    else:
        trend_conflict_summary = "No correctness=1 statements for analysis."

    # 7) Export correctness=1 info to a separate JSON
    correct_info_path = os.path.join(output_dir, f"correct_{selected_subj}_{selected_obj}_{selected_type}.json")
    export_correct_info(pruned_target_statements, correct_info_path)

    # 8) Construct prompt & generate final story with OpenAI
 
    if pruned_target_statements:
        prompt_text = construct_input_for_openai(pruned_target_statements, trend_conflict_summary)
        print("\n=== Prompt for OpenAI (correctness=1 only) ===")
        print(prompt_text[:1000], "...\n")

        story_result = generate_story_with_openai(prompt_text)
        print("\n=== Final Story from OpenAI ===")
        print(story_result)
    else:
        print("[INFO] No correctness=1 statements left; skipping story generation.")


    # 9) Save updated JSON (with correctness=0/1 in evidence)
    save_updated_json(input_file, all_data)

    print("[INFO] Done. correctness=1 data exported, story generated, and JSON updated.")

def filter_incorrect_evidence(statements):
    new_list = []
    for stmt in statements:
        filtered = {
            "id": stmt.get("id"),
            "type": stmt.get("type"),
            "subj": stmt.get("subj", {}),
            "obj": stmt.get("obj", {}),
            "evidence": []
        }
        for ev in stmt.get("evidence", []):
            if ev.get("correctness", 0) == 1:
                filtered["evidence"].append(ev)
        new_list.append(filtered)
    return new_list


if __name__ == "__main__":
    main()
