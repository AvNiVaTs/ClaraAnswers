"""
pipeline_b.py
Pipeline B: Onboarding transcript -> Patch v1 -> Account Memo v2 -> Agent Spec v2
Run: python workflows/pipeline_b.py --account_id account_001 --transcript data/transcripts/account_001_onboarding.txt
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.patch import run as patch_run
from scripts.generate_prompt import run as generate_run


def run_pipeline_b(account_id: str, onboarding_transcript_path: str):
    print(f"\n{'='*50}")
    print(f"🔄 Pipeline B: Onboarding -> Agent v2")
    print(f"   Account: {account_id}")
    print(f"   Transcript: {onboarding_transcript_path}")
    print(f"{'='*50}")

    v1_dir = f"outputs/accounts/{account_id}/v1"
    v2_dir = f"outputs/accounts/{account_id}/v2"

    # Check v1 exists
    if not os.path.exists(f"{v1_dir}/account_memo.json"):
        print(f"❌ Error: v1 memo not found at {v1_dir}/account_memo.json")
        print("   Please run Pipeline A first.")
        sys.exit(1)

    # Step 1: Extract patch and apply to produce v2 memo
    v2_memo, patch_result = patch_run(
        account_id=account_id,
        v1_memo_path=f"{v1_dir}/account_memo.json",
        onboarding_transcript_path=onboarding_transcript_path,
        v2_output_dir=v2_dir,
        changelog_dir="changelog"
    )

    # Step 2: Generate v2 agent spec
    spec = generate_run(
        memo_path=f"{v2_dir}/account_memo.json",
        output_dir=v2_dir,
        version="v2"
    )

    changes = len(patch_result.get("changelog", []))
    print(f"\n✅ Pipeline B complete for {account_id}")
    print(f"   📄 v2 Memo:    {v2_dir}/account_memo.json")
    print(f"   🤖 v2 Spec:    {v2_dir}/agent_spec.json")
    print(f"   📝 Changelog:  changelog/{account_id}_changelog.md")
    print(f"   🔢 Changes:    {changes} fields updated")
    print(f"{'='*50}\n")

    return v2_memo, spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline B: Onboarding -> Agent v2")
    parser.add_argument("--account_id", required=True)
    parser.add_argument("--transcript", required=True, help="Path to onboarding transcript file")
    args = parser.parse_args()

    run_pipeline_b(args.account_id, args.transcript)
