"""
pipeline_a.py
Pipeline A: Demo call transcript -> Account Memo v1 -> Agent Spec v1
Run: python workflows/pipeline_a.py --account_id account_001 --transcript data/transcripts/account_001_demo.txt
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.extract import run as extract_run
from scripts.generate_prompt import run as generate_run


def run_pipeline_a(account_id: str, transcript_path: str):
    print(f"\n{'='*50}")
    print(f"🚀 Pipeline A: Demo Call -> Agent v1")
    print(f"   Account: {account_id}")
    print(f"   Transcript: {transcript_path}")
    print(f"{'='*50}")

    output_dir = f"outputs/accounts/{account_id}/v1"

    # Step 1: Extract account memo
    memo = extract_run(
        account_id=account_id,
        transcript_path=transcript_path,
        output_dir=output_dir
    )

    # Step 2: Generate agent spec
    spec = generate_run(
        memo_path=f"{output_dir}/account_memo.json",
        output_dir=output_dir,
        version="v1"
    )

    print(f"\n✅ Pipeline A complete for {account_id}")
    print(f"   📄 Memo:  {output_dir}/account_memo.json")
    print(f"   🤖 Spec:  {output_dir}/agent_spec.json")
    print(f"{'='*50}\n")

    return memo, spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline A: Demo -> Agent v1")
    parser.add_argument("--account_id", required=True, help="Account ID e.g. account_001")
    parser.add_argument("--transcript", required=True, help="Path to demo transcript file")
    args = parser.parse_args()

    run_pipeline_a(args.account_id, args.transcript)
