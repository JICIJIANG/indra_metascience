import json
import os

# ============================
#  Save updated JSON
# ============================
def save_updated_json(json_path, data):
    backup_path = json_path + ".bak"
    if os.path.exists(json_path):
        os.rename(json_path, backup_path)
        print(f"[INFO] A backup of the old JSON file is created: {backup_path}")
    else:
        print("[WARN] Original JSON file does not exist, cannot create a backup.")

    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Updated JSON saved to: {json_path}")


# ============================
#  Export correctness=1 info to separate JSON
# ============================
def export_correct_info(statements, out_json_path):
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
            output_data.append({
                "stmt_id": st_id,
                "subj": subj,
                "obj": obj,
                "relationship": rtype,
                "pmid": pmid,
                "year": year,
                "evidence_text": text
            })

    with open(out_json_path, "w", encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"[INFO] correctness=1 evidence exported to: {out_json_path}")

# ============================
# Export TSV
# ============================
def export_yearly_counts_to_tsv(counts_by_year, output_dir, selected_type, selected_subj, selected_obj):
    """
    Export a dictionary {year: count} to a TSV file
    """
    os.makedirs(output_dir, exist_ok=True)
    tsv_filename = f"{selected_type}_{selected_subj}_{selected_obj}_yearly_counts.tsv"
    output_tsv_path = os.path.join(output_dir, tsv_filename)

    with open(output_tsv_path, 'w', encoding='utf-8') as f:
        f.write("year\tcount\n")
        for year in sorted(counts_by_year.keys()):
            f.write(f"{year}\t{counts_by_year[year]}\n")

    print(f"[INFO] TSV file exported to: {output_tsv_path}")
