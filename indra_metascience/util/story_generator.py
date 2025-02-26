# indra_metascience/util/story_generator.py

from indra_metascience.api.openai_client import client, query_openai

def generate_story_from_statements(pruned_statements, trend_conflict_summary):
    """
    Combine correctness=1 statements and a trend_conflict_summary to construct a prompt,
    then call OpenAI to generate the final story.
    """
    if not pruned_statements:
        return "[INFO] No correctness=1 statements left; skipping story generation."

    # Build the prompt
    combined_evidence = []
    for statement in pruned_statements:
        rtype = statement.get("type", "Unknown type")
        subj = statement.get("subj", {}).get("name", "Unknown subject")
        obj = statement.get("obj", {}).get("name", "Unknown object")
        ev_list = statement.get("evidence", [])
        ev_texts = []
        for ev in ev_list:
            if ev.get("correctness", 0) == 1:
                year = ev.get("year", "unknown year")
                pmid = ev.get("pmid", "unknown PMID")
                text = ev.get("text", "No evidence text")
                ev_texts.append(f"In {year} (PMID: {pmid}): {text}")

        evidence_str = " ".join(ev_texts)
        combined_evidence.append(
            f"The '{rtype}' relationship between {subj} and {obj} is supported by:\n{evidence_str}"
        )

    prompt_text = (
        "Below are several correctness=1 evidences describing a biological relationship:\n\n"
        + "\n".join(combined_evidence)
        + "\n\nAdditionally, we have a trend/conflict analysis:\n"
        + trend_conflict_summary
        + "\nPlease produce a coherent scientific story discussing:\n"
        + "1) The studied relationship,\n"
        + "2) New discoveries,\n"
        + "3) Possible reasons for interest shifts.\n"
        + "Use an objective and scholarly tone.\n"
        + "===============================================\n"
    )

    # Call OpenAI via our query_openai function
    try:
        story_text = query_openai(prompt_text, temperature=0.7, max_tokens=1024)
        return story_text
    except Exception as e:
        print(f"[ERROR] OpenAI story generation failed: {e}")
        return "[ERROR] No story returned due to error."
