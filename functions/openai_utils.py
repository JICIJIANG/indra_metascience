from .openai_config import client

# ============================
# 7) Use OpenAI ChatCompletion to check correctness
# ============================
def check_correctness_with_openai(evidence_text, subj, obj, relationship):
    """
    Send a short prompt to OpenAI, expect 'Yes' or 'No' answer.
    """
    prompt_content = f"""You need to check if the following sentence implies the statement.
Sentence: "{evidence_text}"
Statement: "{subj} {relationship} {obj}"
Only answer "Yes" or "No".
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_content}],
            temperature=0.0,
            max_tokens=5
        )
        ans_text = response.choices[0].message.content.strip()
        return "Yes" if ans_text.lower().startswith("yes") else "No"
    except Exception as e:
        print(f"[ERROR] OpenAI correctness check failed: {e}")
        return "No"


# ============================
# 8) Evaluate correctness for each statement with OpenAI
# ============================
def assess_evidence_vs_statement(statement):
    subj = statement.get("subj", {}).get("name", "")
    obj = statement.get("obj", {}).get("name", "")
    rtype = statement.get("type", "")
    evidence_list = statement.get("evidence", [])

    correct_count = 0
    for ev in evidence_list:
        text = ev.get("text", "")
        ans = check_correctness_with_openai(text, subj, obj, rtype)
        if ans.lower().startswith("yes"):
            ev["correctness"] = 1
            correct_count += 1
        else:
            ev["correctness"] = 0

    print(f"[INFO] Statement [{subj} {rtype} {obj}] => total={len(evidence_list)}, "
          f"correct={correct_count}, incorrect={len(evidence_list)-correct_count}")


# ============================
# 6) Build prompt for OpenAI
# ============================
def construct_input_for_openai(statements, trend_conflict_summary):
    combined_evidence = []
    for statement in statements:
        rtype = statement.get("type", "Unknown type")
        subj = statement.get("subj", {}).get("name", "Unknown subject")
        obj = statement.get("obj", {}).get("name", "Unknown object")
        ev_list = statement.get("evidence", [])

        ev_texts = []
        for ev in ev_list:
            year = ev.get("year", "unknown year")
            pmid = ev.get("pmid", "unknown PMID")
            text = ev.get("text", "No evidence text")
            ev_texts.append(f"In {year} (PMID: {pmid}): {text}")

        evidence_str = " ".join(ev_texts)
        combined_evidence.append(
            f"The '{rtype}' relationship between {subj} and {obj} is supported by:\n{evidence_str}"
        )

    body_text = (
        "Below are several correctness=1 evidences describing a biological relationship:\n\n"
        + "\n".join(combined_evidence)
        + "\n\n"
        + "Additionally, we have a trend/conflict analysis:\n"
        + trend_conflict_summary
        + "\n"
        + "Please produce a coherent scientific story discussing:\n"
        + "1) The studied relationship,\n"
        + "2) New discoveries,\n"
        + "3) Possible reasons for interest shifts.\n"
        + "Use an objective and scholarly tone.\n"
        + "===============================================\n"
    )
    return body_text


def generate_story_with_openai(prompt_text):
    """
    Use OpenAI ChatCompletion to generate a final story from a large prompt.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] OpenAI story generation failed: {e}")
        return "No story returned due to error."
