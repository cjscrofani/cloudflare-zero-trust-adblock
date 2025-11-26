#!/usr/bin/env python3
"""
Upload AdGuard DNS Filter Lists to Cloudflare Zero Trust via API

This script:
1. Creates Gateway Lists in Cloudflare Zero Trust
2. Uploads all domain and IP CSV files
3. Creates a single DNS policy that blocks all domains and IPs
"""

import os
import sys
import time
import glob
import argparse
import requests
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration - loaded from .env file
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

# API Configuration
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Rate limiting
RATE_LIMIT_DELAY = 1  # seconds between API calls


def check_config():
    """Verify configuration is set."""
    if not ACCOUNT_ID or not API_TOKEN:
        print("❌ ERROR: Missing Cloudflare credentials")
        print("\nPlease create a .env file with your credentials:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("\n2. Edit .env and add your values:")
        print("   CLOUDFLARE_ACCOUNT_ID=your-account-id")
        print("   CLOUDFLARE_API_TOKEN=your-api-token")
        print("\nHow to get these values:")
        print("  • Account ID: Cloudflare Dashboard → Zero Trust → Settings")
        print("  • API Token: Cloudflare Dashboard → My Profile → API Tokens")
        print("    - Click 'Create Token'")
        print("    - Use 'Edit Cloudflare Zero Trust' template")
        sys.exit(1)

    if ACCOUNT_ID == "your-account-id-here" or API_TOKEN == "your-api-token-here":
        print("❌ ERROR: Please update the values in your .env file")
        print("   Don't use the placeholder values from .env.example")
        sys.exit(1)


def get_existing_lists() -> Dict[str, str]:
    """
    Get all existing Gateway Lists.
    Returns a dict mapping list names to list IDs.
    """
    url = f"{BASE_URL}/gateway/lists"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        lists = response.json()["result"]
        return {list_item["name"]: list_item["id"] for list_item in lists}
    else:
        return {}


def get_existing_dns_policies() -> Dict[str, str]:
    """
    Get all existing DNS Gateway Rules/Policies.
    Returns a dict mapping policy names to policy IDs.
    """
    url = f"{BASE_URL}/gateway/rules"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        rules = response.json()["result"]
        return {rule["name"]: rule["id"] for rule in rules}
    else:
        return {}


def delete_existing_adguard_policy(auto_approve=False) -> bool:
    """
    Delete any existing AdGuard DNS policy.
    This must be done BEFORE deleting lists, as lists referenced by policies cannot be deleted.

    Returns True if a policy was deleted or none existed.
    """
    print("Checking for existing AdGuard DNS policy...")

    existing_policies = get_existing_dns_policies()
    adguard_policy_name = "Block AdGuard DNS Filter"

    if adguard_policy_name in existing_policies:
        policy_id = existing_policies[adguard_policy_name]
        print(f"Found existing policy: {adguard_policy_name}")

        if auto_approve:
            print("Auto-approving policy deletion (--auto-approve enabled)")
        else:
            response = input("Delete this policy before proceeding? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("⚠️  Warning: Cannot delete lists while policy references them")
                return False

        url = f"{BASE_URL}/gateway/rules/{policy_id}"
        del_response = requests.delete(url, headers=HEADERS)

        if del_response.status_code == 200:
            print(f"  ✅ Deleted policy: {adguard_policy_name}")
            time.sleep(RATE_LIMIT_DELAY)  # Give API time to process
            return True
        else:
            print(f"  ❌ Failed to delete policy: {adguard_policy_name}")
            print(f"     Status: {del_response.status_code}")
            print(f"     Response: {del_response.text}")
            return False
    else:
        print("No existing AdGuard DNS policy found")
        return True


def delete_existing_adguard_lists(auto_approve=False):
    """Delete any existing AdGuard lists to allow fresh upload."""
    print("Checking for existing AdGuard lists...")

    existing_lists = get_existing_lists()
    adguard_lists = {name: list_id for name, list_id in existing_lists.items()
                     if name.startswith("AdGuard ")}

    if adguard_lists:
        print(f"Found {len(adguard_lists)} existing AdGuard lists")

        if auto_approve:
            response = 'yes'
            print("Auto-approving deletion (--auto-approve enabled)")
        else:
            response = input("Delete these lists before uploading? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            for name, list_id in adguard_lists.items():
                url = f"{BASE_URL}/gateway/lists/{list_id}"
                del_response = requests.delete(url, headers=HEADERS)

                if del_response.status_code == 200:
                    print(f"  ✅ Deleted: {name}")
                else:
                    print(f"  ❌ Failed to delete: {name}")

            print()
        else:
            print("⚠️  Warning: Existing lists may cause conflicts")
            print()


def create_gateway_list(name: str, list_type: str, description: str) -> str:
    """
    Create a Gateway List.

    Args:
        name: List name
        list_type: "HOSTNAME" or "IP"
        description: List description

    Returns:
        List ID
    """
    url = f"{BASE_URL}/gateway/lists"
    data = {
        "name": name,
        "type": list_type,
        "description": description
    }

    response = requests.post(url, headers=HEADERS, json=data)

    if response.status_code == 200:
        list_id = response.json()["result"]["id"]
        print(f"✅ Created list: {name} (ID: {list_id})")
        return list_id
    else:
        print(f"❌ Failed to create list: {name}")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)


def upload_items_to_list(list_id: str, items: List[str], list_name: str):
    """
    Upload items to a Gateway List using PATCH to append items.

    Args:
        list_id: The list ID
        items: List of domains or IPs
        list_name: Name for logging
    """
    url = f"{BASE_URL}/gateway/lists/{list_id}"

    # Format items for API - PATCH requires "append" operation
    formatted_items = [{"value": item} for item in items]

    payload = {
        "append": formatted_items
    }

    # Use PATCH to append items to the list
    response = requests.patch(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        print(f"   ✅ Uploaded {len(items)} items to {list_name}")
    else:
        print(f"   ❌ Failed to upload items to {list_name}")
        print(f"      Status: {response.status_code}")
        print(f"      Response: {response.text}")
        sys.exit(1)


def read_csv_file(filepath: str) -> List[str]:
    """Read items from CSV file (one item per line)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def create_dns_policy(list_ids: List[str], policy_name: str, domain_list_count: int):
    """
    Create a DNS policy that blocks domains/IPs in all lists.

    Args:
        list_ids: List of Gateway List IDs (domains first, then IPs)
        policy_name: Name for the DNS policy
        domain_list_count: Number of domain lists (vs IP lists)
    """
    url = f"{BASE_URL}/gateway/rules"

    # Build traffic condition
    # Domain lists use: any(dns.domains[*] in $list_id)
    # IP lists use: any(dns.resolved_ips[*] in $list_id)
    conditions = []

    # Add domain list conditions
    for i in range(domain_list_count):
        conditions.append(f'any(dns.domains[*] in ${list_ids[i]})')

    # Add IP list conditions
    for i in range(domain_list_count, len(list_ids)):
        conditions.append(f'any(dns.resolved_ips[*] in ${list_ids[i]})')

    # Combine with OR
    traffic = " or ".join(conditions)

    data = {
        "name": policy_name,
        "description": "Block domains and IPs from AdGuard DNS Filter",
        "enabled": True,
        "action": "block",
        "filters": ["dns"],
        "traffic": traffic,
        "rule_settings": {
            "block_page_enabled": False
        }
    }

    response = requests.post(url, headers=HEADERS, json=data)

    if response.status_code == 200:
        rule_id = response.json()["result"]["id"]
        print(f"\n🎉 SUCCESS! Created DNS policy: {policy_name}")
        print(f"   Policy ID: {rule_id}")
        print(f"   Blocking {len(list_ids)} lists")
        return rule_id
    else:
        print(f"\n❌ Failed to create DNS policy")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)


def main():
    """Main execution."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Upload AdGuard DNS Filter to Cloudflare Zero Trust',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (prompts for confirmation)
  python3 upload_to_cloudflare.py

  # Non-interactive mode (for cron jobs)
  python3 upload_to_cloudflare.py --auto-approve

  # Dry run (show what would be uploaded)
  python3 upload_to_cloudflare.py --dry-run
        """
    )
    parser.add_argument(
        '-y', '--auto-approve',
        action='store_true',
        help='Auto-approve all prompts (non-interactive mode for cron jobs)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be uploaded without making changes'
    )
    args = parser.parse_args()

    print("=" * 70)
    print("Cloudflare Zero Trust - AdGuard DNS Filter Upload")
    print("=" * 70)
    if args.auto_approve:
        print("Running in AUTO-APPROVE mode (non-interactive)")
    if args.dry_run:
        print("DRY RUN mode - no changes will be made")
    print()

    # Check configuration
    check_config()

    if args.dry_run:
        print("DRY RUN: Skipping actual upload")
        return 0

    # Delete existing policy FIRST (lists cannot be deleted while referenced by a policy)
    if not delete_existing_adguard_policy(args.auto_approve):
        print("❌ Cannot proceed without deleting existing policy")
        sys.exit(1)

    # Now delete existing AdGuard lists
    delete_existing_adguard_lists(args.auto_approve)

    # Find all CSV files in the lists/ directory
    domain_files = sorted(glob.glob("lists/adguard_domains_*.csv"))
    ip_files = sorted(glob.glob("lists/adguard_ips_*.csv"))

    if not domain_files and not ip_files:
        print("❌ No CSV files found. Run 'python3 generate-lists.py' first.")
        sys.exit(1)

    print(f"Found {len(domain_files)} domain files and {len(ip_files)} IP files")
    print()

    # Confirm before proceeding
    print("This will:")
    print(f"  - Create {len(domain_files)} domain lists in Cloudflare")
    print(f"  - Create {len(ip_files)} IP lists in Cloudflare")
    print(f"  - Create 1 DNS policy blocking all lists")
    print()

    if args.auto_approve:
        print("Auto-approving upload (--auto-approve enabled)")
    else:
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)

    print()
    print("=" * 70)
    print("Step 1: Creating and uploading domain lists")
    print("=" * 70)

    list_ids = []

    # Process domain files
    for i, filepath in enumerate(domain_files, 1):
        filename = os.path.basename(filepath)
        list_name = f"AdGuard Domains - Part {i}"

        print(f"\n[{i}/{len(domain_files)}] Processing {filename}...")

        # Read domains
        domains = read_csv_file(filepath)

        # Create list
        list_id = create_gateway_list(
            name=list_name,
            list_type="DOMAIN",
            description=f"AdGuard DNS Filter domains - Part {i} of {len(domain_files)}"
        )
        list_ids.append(list_id)

        # Upload items
        upload_items_to_list(list_id, domains, list_name)

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

    # Process IP files
    if ip_files:
        print()
        print("=" * 70)
        print("Step 2: Creating and uploading IP lists")
        print("=" * 70)

        for i, filepath in enumerate(ip_files, 1):
            filename = os.path.basename(filepath)
            list_name = f"AdGuard IPs - Part {i}"

            print(f"\n[{i}/{len(ip_files)}] Processing {filename}...")

            # Read IPs
            ips = read_csv_file(filepath)

            # Create list
            list_id = create_gateway_list(
                name=list_name,
                list_type="IP",
                description=f"AdGuard DNS Filter IP addresses - Part {i} of {len(ip_files)}"
            )
            list_ids.append(list_id)

            # Upload items
            upload_items_to_list(list_id, ips, list_name)

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

    # Create DNS policy
    print()
    print("=" * 70)
    print("Step 3: Creating DNS Policy")
    print("=" * 70)

    policy_name = "Block AdGuard DNS Filter"
    create_dns_policy(list_ids, policy_name, len(domain_files))

    # Summary
    print()
    print("=" * 70)
    print("🎉 ALL DONE!")
    print("=" * 70)
    print(f"✅ Created {len(domain_files)} domain lists")
    print(f"✅ Created {len(ip_files)} IP lists")
    print(f"✅ Created 1 DNS policy: '{policy_name}'")
    print()
    print("Next steps:")
    print("1. Go to Cloudflare Zero Trust Dashboard")
    print("2. Navigate to Gateway > Firewall Policies > DNS")
    print(f"3. You should see the policy: '{policy_name}'")
    print("4. The policy is enabled and blocking traffic!")
    print()
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
