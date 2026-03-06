"""
generate_prompt.py
Pipeline A - Step 2: Generate Retell Agent Draft Spec from account memo using Groq.
"""

import os
import json
import re
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])

PROMPT_GENERATOR_TEMPLATE = """\
You are a prompt engineer for Clara Answers, an AI voice agent for service trade businesses.

Given the account memo below, generate a complete Retell Agent Draft Spec as JSON.

RULES:
- Never mention "function calls", "tools", or "AI" to the caller.
- Do not ask unnecessary questions. Only collect what is needed for routing.
- Business hours flow must include: greeting, ask purpose, collect name and number, transfer or route, fallback if transfer fails, ask if anything else, close.
- After hours flow must include: greeting, ask purpose, confirm if emergency, if emergency collect name/number/address immediately then attempt transfer, fallback if transfer fails with assurance of follow-up, if non-emergency collect details and confirm next business day follow-up, ask if anything else, close.
- Keep tone warm, professional, concise.
- Return ONLY valid JSON. No markdown, no explanation, no backticks.

Generate this schema:

{{
  "agent_name": "string",
  "version": "{version}",
  "voice_style": "professional, warm, concise",
  "key_variables": {{
    "timezone": "string or unknown",
    "business_hours": "string",
    "business_days": "string",
    "transfer_number": "string or TBD",
    "company_name": "string",
    "owner_name": "string or unknown",
    "emergency_clients": "string or none"
  }},
  "system_prompt": "FULL multi-paragraph agent prompt covering both flows",
  "business_hours_flow": {{
    "greeting": "string",
    "ask_purpose": "string",
    "collect_info": "string",
    "transfer_action": "string",
    "transfer_fail": "string",
    "anything_else": "string",
    "close": "string"
  }},
  "after_hours_flow": {{
    "greeting": "string",
    "ask_purpose": "string",
    "confirm_emergency": "string",
    "emergency_collect": "string",
    "emergency_transfer": "string",
    "emergency_transfer_fail": "string",
    "non_emergency_collect": "string",
    "non_emergency_confirm": "string",
    "anything_else": "string",
    "close": "string"
  }},
  "call_transfer_protocol": "string describing transfer logic",
  "fallback_protocol": "string describing what happens if transfer fails",
  "pricing_disclosure": "string - when and how to mention pricing if asked",
  "tool_invocation_placeholders": ["list of background actions e.g. log_call, send_sms"],
  "notes": "string"
}}

ACCOUNT MEMO:
{memo}
"""

def generate_agent_spec(memo: dict, version: str = "v1") -> dict:
    prompt = PROMPT_GENERATOR_TEMPLATE.format(
        version=version,
        memo=json.dumps(memo, indent=2)
    )

    print(f"Generating agent spec (version: {version})...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an AI voice agent prompt engineer. Always return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    raw = response.choices[0].message.content.strip()

    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print("Raw response:", raw[:500])
        raise

    spec["version"] = version
    return spec


def run(memo_path: str, output_dir: str, version: str = "v1"):
    memo = json.loads(Path(memo_path).read_text(encoding="utf-8"))
    spec = generate_agent_spec(memo, version)

    output_path = Path(output_dir) / "agent_spec.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(spec, f, indent=2)

    print(f"Agent spec saved to {output_path}")
    return spec


if __name__ == "__main__":
    run(
        memo_path="outputs/accounts/account_001/v1/account_memo.json",
        output_dir="outputs/accounts/account_001/v1",
        version="v1"
    )