#!/bin/bash
# Railway Cron Job Start Script
# This script runs the AdGuard DNS filter update process

set -e  # Exit on any error

echo "=========================================="
echo "AdGuard DNS Filter Update - Railway Cron"
echo "=========================================="
echo "Started at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Step 1: Generate lists from AdGuard filter
echo "Step 1: Generating domain/IP lists..."
python3 generate-lists.py

# Step 2: Upload to Cloudflare (non-interactive mode)
echo ""
echo "Step 2: Uploading to Cloudflare..."
python3 upload_to_cloudflare.py --auto-approve

echo ""
echo "=========================================="
echo "Completed at: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="
