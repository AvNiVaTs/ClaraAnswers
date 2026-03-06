"""
run_all.py
Batch runner - runs Pipeline A and/or B on all accounts in data/transcripts/
Naming convention:
  - account_001_demo.txt        -> Pipeline A
  - account_001_onboarding.txt  -> Pipeline B (requires v1 to exist)

Run: python run_all.py
"""

import os
import sys
import glob
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.pipeline_a import run_pipeline_a
from workflows.pipeline_b import run_pipeline_b

TRANSCRIPT_DIR = "data/transcripts"

def get_accounts():
    files = glob.glob(f"{TRANSCRIPT_DIR}/*.txt")
    accounts = {}

    for f in files:
        basename = os.path.basename(f)
        match = re.match(r"(account_\d+)_(demo|onboarding)\.txt", basename)
        if match:
            account_id = match.group(1)
            call_type = match.group(2)
            if account_id not in accounts:
                accounts[account_id] = {}
            accounts[account_id][call_type] = f

    return accounts

def main():
    accounts = get_accounts()

    if not accounts:
        print("❌ No transcripts found in data/transcripts/")
        print("   Expected format: account_001_demo.txt, account_001_onboarding.txt")
        sys.exit(1)

    print(f"\n📂 Found {len(accounts)} account(s): {list(accounts.keys())}")
    results = {"success": [], "failed": []}

    for account_id, files in sorted(accounts.items()):
        # Run Pipeline A first if demo exists
        if "demo" in files:
            try:
                run_pipeline_a(account_id, files["demo"])
                results["success"].append(f"{account_id} v1")
            except Exception as e:
                print(f"❌ Pipeline A failed for {account_id}: {e}")
                results["failed"].append(f"{account_id} v1: {e}")

        # Then Pipeline B if onboarding exists
        if "onboarding" in files:
            try:
                run_pipeline_b(account_id, files["onboarding"])
                results["success"].append(f"{account_id} v2")
            except Exception as e:
                print(f"❌ Pipeline B failed for {account_id}: {e}")
                results["failed"].append(f"{account_id} v2: {e}")

    print(f"\n{'='*50}")
    print(f"📊 Batch Summary")
    print(f"   ✅ Success: {len(results['success'])} - {results['success']}")
    if results["failed"]:
        print(f"   ❌ Failed:  {len(results['failed'])} - {results['failed']}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
