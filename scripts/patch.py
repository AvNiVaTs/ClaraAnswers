"""
patch.py
Pipeline B - Step 1: Extract updates from onboarding transcript and patch v1 memo -> v2.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

PATCH_PROMPT_TEMPLATE = """\
You are a configuration assistant for Clara Answers.

You will receive:
1. An existing v1 account memo (already configured from demo call)
2. A new onboarding call transcript with updated or additional information

Your job is to:
- Extract ONLY the fields that are NEW or CHANGED in the onboarding transcript
- Return a patch object with just those fields
- For each changed field, explain WHY it changed in the changelog

RULES:
- Do not re-extract fields that have not changed
- Do not invent information
- If something is now resolved that was previously in questions_or_unknowns, move it to the correct field
- Return ONLY valid JSON. No markdown, no explanation, no backticks.

Return this schema:

{{
  "patch": {{
  }},
  "changelog": [
    {{
      "field": "field name",
      "old_value": "previous value or null if new",
      "new_value": "updated value",
      "reason": "why this changed based on onboarding transcript"
    }}
  ],
  "resolved_unknowns": ["list of questions_or_unknowns that are now answered"],
  "new_unknowns": ["list of any new questions that came up"]
}}

V1 ACCOUNT MEMO:
{v1_memo}

ONBOARDING TRANSCRIPT:
{transcript}
"""

def extract_patch(v1_memo: dict, transcript_path: str) -> dict:
    transcript = Path(transcript_path).read_text(encoding="utf-8")

    prompt = PATCH_PROMPT_TEMPLATE.format(
        v1_memo=json.dumps(v1_memo, indent=2),
        transcript=transcript
    )

    print("Sending onboarding transcript to Groq for patch extraction...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a structured data patching assistant. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()

    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:", raw[:500])
        raise

    return result


def apply_patch(v1_memo: dict, patch: dict) -> dict:
    v2_memo = json.loads(json.dumps(v1_memo))

    def deep_merge(base, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                deep_merge(base[key], value)
            else:
                base[key] = value

    deep_merge(v2_memo, patch)
    return v2_memo


def generate_changelog_md(account_id: str, changelog: list, resolved: list, new_unknowns: list) -> str:
    lines = [
        f"# Changelog: {account_id}",
        f"**Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Version:** v1 -> v2",
        "",
        "## Changes",
    ]

    for item in changelog:
        lines.append(f"\n### {item['field']}")
        lines.append(f"- **Old:** {item['old_value']}")
        lines.append(f"- **New:** {item['new_value']}")
        lines.append(f"- **Reason:** {item['reason']}")

    if resolved:
        lines.append("\n## Resolved Unknowns")
        for r in resolved:
            lines.append(f"- {r}")

    if new_unknowns:
        lines.append("\n## New Unknowns")
        for u in new_unknowns:
            lines.append(f"- {u}")

    return "\n".join(lines)


def run(account_id: str, v1_memo_path: str, onboarding_transcript_path: str,
        v2_output_dir: str, changelog_dir: str):

    print(f"\nRunning patch for {account_id}...")

    v1_memo = json.loads(Path(v1_memo_path).read_text(encoding="utf-8"))
    patch_result = extract_patch(v1_memo, onboarding_transcript_path)

    patch = patch_result.get("patch", {})
    changelog = patch_result.get("changelog", [])
    resolved = patch_result.get("resolved_unknowns", [])
    new_unknowns = patch_result.get("new_unknowns", [])

    v2_memo = apply_patch(v1_memo, patch)

    Path(v2_output_dir).mkdir(parents=True, exist_ok=True)
    v2_memo_path = Path(v2_output_dir) / "account_memo.json"
    with open(v2_memo_path, "w") as f:
        json.dump(v2_memo, f, indent=2)

    Path(changelog_dir).mkdir(parents=True, exist_ok=True)
    changelog_md = generate_changelog_md(account_id, changelog, resolved, new_unknowns)
    changelog_path = Path(changelog_dir) / f"{account_id}_changelog.md"
    with open(changelog_path, "w") as f:
        f.write(changelog_md)

    patch_path = Path(changelog_dir) / f"{account_id}_patch.json"
    with open(patch_path, "w") as f:
        json.dump(patch_result, f, indent=2)

    print(f"v2 memo saved to {v2_memo_path}")
    print(f"Changelog saved to {changelog_path}")

    return v2_memo, patch_result


if __name__ == "__main__":
    run(
        account_id="account_001",
        v1_memo_path="outputs/accounts/account_001/v1/account_memo.json",
        onboarding_transcript_path="data/transcripts/account_001_onboarding.txt",
        v2_output_dir="outputs/accounts/account_001/v2",
        changelog_dir="changelog"
    )