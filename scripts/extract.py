"""
extract.py
Pipeline A - Step 1: Extract structured account memo from transcript using Groq.
"""

import os
import json
import re
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

EXTRACTION_PROMPT_TEMPLATE = """\
You are a configuration assistant for Clara Answers, an AI voice agent platform for service trade businesses.

You will be given a transcript of a demo or onboarding call. Your job is to extract structured configuration data.

RULES:
- Only extract what is EXPLICITLY stated. Do not invent or assume.
- If something is missing or unclear, add it to "questions_or_unknowns".
- Return ONLY valid JSON. No markdown, no explanation, no backticks.

Extract the following schema (replace placeholder text with real extracted values):

{{
  "account_id": "{account_id}",
  "company_name": "string or null",
  "owner_name": "string or null",
  "contact_email": "string or null",
  "contact_phone": "string or null",
  "business_hours": {{
    "days": "string or null",
    "start": "string or null",
    "end": "string or null",
    "timezone": "string or null"
  }},
  "office_address": "string or null",
  "services_supported": ["list of strings"],
  "pricing_info": "string or null",
  "emergency_definition": ["list of what counts as an emergency"],
  "emergency_routing_rules": {{
    "primary_contact": "string or null",
    "transfer_number": "string or null",
    "fallback": "string or null",
    "special_clients": ["list of any VIP/special emergency clients with details"]
  }},
  "non_emergency_routing_rules": "string or null",
  "call_transfer_rules": {{
    "transfer_on": "string or null",
    "timeout": "string or null",
    "transfer_fail_action": "string or null"
  }},
  "integration_constraints": ["list of strings or empty"],
  "after_hours_flow_summary": "string or null",
  "office_hours_flow_summary": "string or null",
  "call_forwarding_setup": "string or null",
  "second_number_status": "string or null",
  "questions_or_unknowns": ["list of genuinely missing config details"],
  "notes": "string - short summary of the call"
}}

ACCOUNT_ID: {account_id}

TRANSCRIPT:
{transcript}
"""

def extract_account_memo(transcript_path: str, account_id: str) -> dict:
    transcript = Path(transcript_path).read_text(encoding="utf-8")

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(
        account_id=account_id,
        transcript=transcript
    )

    print("Sending transcript to Groq for extraction...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a structured data extraction assistant. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        memo = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:", raw[:500])
        raise

    return memo


def run(account_id: str, transcript_path: str, output_dir: str):
    print(f"\nExtracting account memo for {account_id}...")
    memo = extract_account_memo(transcript_path, account_id)

    output_path = Path(output_dir) / "account_memo.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(memo, f, indent=2)

    print(f"Account memo saved to {output_path}")
    return memo


if __name__ == "__main__":
    run(
        account_id="account_001",
        transcript_path="data/transcripts/account_001_demo.txt",
        output_dir="outputs/accounts/account_001/v1"
    )