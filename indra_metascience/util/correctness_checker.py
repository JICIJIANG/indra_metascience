# indra_metascience/util/correctness_checker.py

import json
import os
from collections import Counter

# Importing the same client object and the query_openai function
from indra_metascience.api.openai_client import client, query_openai

def check_correctness_with_openai(evidence_text, subj, obj, relationship):
    """
    Use OpenAI to check whether 'evidence_text' supports the statement "subj relationship obj".
    Returns "Yes" or "No" only.
    """
    prompt_content = f"""You need to check if the following sentence implies the statement.
Sentence: "{evidence_text}"
Statement: "{subj} {relationship} {obj}"
Only answer "Yes" or "No".
"""
    try:
        # Now use query_openai instead of calling client.chat.completions.create
        ans_text = query_openai(prompt_content, temperature=0.0, max_tokens=5)
        return "Yes" if ans_text.lower().startswith("yes") else "No"
    except Exception as e:
        print(f"[ERROR] OpenAI correctness check failed: {e}")
        return "No"

def assess_and_filter_correctness(statements):
    """
    Iterates over a list of statements:
      1) Uses 'check_correctness_with_openai' to label each evidence with correctness=0/1.
      2) Retains only those pieces of evidence with correctness=1 (does not remove the statement itself).
    Returns (updated statements, pruned statements where correctness=1 only).

    Note: 'pruned statements' refer to the same set of statement entries but containing only the evidence 
          items with correctness=1 in their evidence list.
    """
    pruned_statements = []
    for stmt in statements:
        subj = stmt.get("subj", {}).get("name", "")
        obj = stmt.get("obj", {}).get("name", "")
        rtype = stmt.get("type", "")
        evidence_list = stmt.get("evidence", [])

        correct_count = 0
        for ev in evidence_list:
            text = ev.get("text", "")
            ans = check_correctness_with_openai(text, subj, obj, rtype)
            if ans.lower().startswith("yes"):
                ev["correctness"] = 1
                correct_count += 1
            else:
                ev["correctness"] = 0

        # Print summary information
        print(f"[INFO] Statement [{subj} {rtype} {obj}] => total={len(evidence_list)}, "
              f"correct={correct_count}, incorrect={len(evidence_list)-correct_count}")

        # Create a statement copy with only correctness=1 evidence
        stmt_pruned = {
            "id": stmt.get("id"),
            "type": stmt.get("type"),
            "subj": stmt.get("subj", {}),
            "obj": stmt.get("obj", {}),
            "evidence": [ev for ev in evidence_list if ev.get("correctness", 0) == 1]
        }
        pruned_statements.append(stmt_pruned)

    return statements, pruned_statements

def export_correct_info(statements, out_json_path):
    """
    Export statements/evidences with correctness=1 to a separate JSON file for subsequent analysis.
    """
    output_data = []
    for stmt in statements:
        st_id = stmt.get("id", "")
        subj = stmt.get("subj", {}).get("name", "")
        obj = stmt.get("obj", {}).get("name", "")
        rtype = stmt.get("type", "")
        for ev in stmt.get("evidence", []):
            pmid = ev.get("pmid", "")
            year = ev.get("year", "")
            text = ev.get("text", "")
            if ev.get("correctness", 0) == 1:
                output_data.append({
                    "stmt_id": st_id,
                    "subj": subj,
                    "obj": obj,
                    "relationship": rtype,
                    "pmid": pmid,
                    "year": year,
                    "evidence_text": text
                })

    os.makedirs(os.path.dirname(out_json_path), exist_ok=True)
    with open(out_json_path, "w", encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] correctness=1 evidence exported to: {out_json_path}")
