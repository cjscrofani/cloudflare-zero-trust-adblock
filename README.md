# AdGuard DNS Filter → Cloudflare Zero Trust (Railway Deployment)

Automated deployment of [AdGuard DNS Filter](https://github.com/AdguardTeam/FiltersRegistry) to Cloudflare Zero Trust Gateway using Railway's cron job service.

> **Warning:** This blocklist is comprehensive (144K+ domains) and may impact website functionality. Test in a controlled environment before deploying broadly.

## Overview

This branch is configured for **Railway deployment** with automated cron-based updates. Railway runs the update process on a schedule, keeping your Cloudflare DNS firewall in sync with the latest AdGuard filter.

**What it does:**
- Downloads the latest AdGuard DNS filter (144K+ domains, 66 IPs)
- Generates Cloudflare-compatible lists (1,000 entries each)
- Uploads to Cloudflare Zero Trust via API
- Creates/updates a single DNS policy blocking all entries

## Railway Deployment

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/cfzt-adblock-dns-firewall.git
cd cfzt-adblock-dns-firewall
git checkout railway-deployment
```

### 2. Create a Railway Project

1. Go to [Railway](https://railway.app) and sign in
2. Click **New Project** → **Deploy from GitHub repo**
3. Select this repository and the `railway-deployment` branch

### 3. Configure Environment Variables

In your Railway project, go to **Variables** and add:

| Variable | Description |
|----------|-------------|
| `CLOUDFLARE_ACCOUNT_ID` | Your Cloudflare Zero Trust account ID |
| `CLOUDFLARE_API_TOKEN` | API token with "Edit Cloudflare Zero Trust" permissions |

**How to get credentials:**
- **Account ID:** Cloudflare Dashboard → Zero Trust → Settings → Account ID
- **API Token:** Cloudflare Dashboard → My Profile → API Tokens → Create Token → Use "Edit Cloudflare Zero Trust" template

### 4. Set Up Cron Schedule

1. In Railway, go to your service **Settings**
2. Find **Cron Schedule** section
3. Enter your desired schedule in cron format:

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Daily at 2 AM UTC | `0 2 * * *` | Recommended |
| Weekly (Sunday 2 AM) | `0 2 * * 0` | Lower frequency |
| Every 6 hours | `0 */6 * * *` | More frequent updates |

4. Save the settings

### 5. Deploy

Railway will automatically deploy when you push changes. For the initial deployment:

1. Railway builds the project using Nixpacks
2. On each cron trigger, it runs `start.sh`
3. The script generates lists and uploads to Cloudflare

## Configuration

### Railway Files

| File | Purpose |
|------|---------|
| `railway.json` | Railway deployment configuration |
| `start.sh` | Entry point script for cron execution |
| `requirements.txt` | Python dependencies (auto-installed) |

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "bash start.sh",
    "restartPolicyType": "NEVER"
  }
}
```

- **NIXPACKS**: Auto-detects Python and installs dependencies
- **restartPolicyType: NEVER**: Ensures the job runs once per cron trigger and exits

### Enterprise Plan (5,000 entries per list)

Edit `generate-lists.py` line 20:

```python
MAX_DOMAINS_PER_LIST = 5000
```

This reduces lists from 145 to ~30.

## Manual Trigger

To run the update manually outside the cron schedule:

1. Go to your Railway service
2. Click **Deploy** → **Trigger Deploy**

Or redeploy from the **Deployments** tab.

## Monitoring

### View Logs

1. Go to your Railway service
2. Click **Deployments** → Select a deployment
3. View the **Logs** tab

Successful runs show:
```
==========================================
AdGuard DNS Filter Update - Railway Cron
==========================================
Started at: 2024-01-15 02:00:00 UTC

Step 1: Generating domain/IP lists...
Fetching filter list from: https://raw.githubusercontent.com/...
Downloaded 180237 lines
Processed 144452 unique domains and 66 unique IPs
...

Step 2: Uploading to Cloudflare...
Auto-approve mode enabled. Proceeding without prompts.
Creating 145 domain lists...
Creating 1 IP list...
Creating DNS policy...
Done!

==========================================
Completed at: 2024-01-15 02:05:23 UTC
==========================================
```

### Notifications (Optional)

Configure Railway notifications in **Project Settings** → **Integrations** to receive alerts on deployment failures.

## Troubleshooting

### Deployment Fails to Build

**Check requirements.txt exists:**
```
requests
python-dotenv
```

### Missing Environment Variables

Error: `Missing Cloudflare credentials`

Ensure both `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` are set in Railway Variables.

### API Errors

**"A resource with this identifier already exists"**

The script handles this automatically with `--auto-approve`. If issues persist, manually delete lists in Cloudflare Zero Trust → Lists.

**"cannot have list with over 1000 items"**

You're on Cloudflare Standard plan. Keep `MAX_DOMAINS_PER_LIST = 1000` (default).

### Cron Not Running

1. Verify cron schedule is set in Railway service settings
2. Check the schedule format is valid (e.g., `0 2 * * *`)
3. Ensure the service is not paused

## Cost

- **Railway**: Cron jobs are billed per execution time. This job typically runs 2-5 minutes.
- **Cloudflare Zero Trust**: Free tier supports Gateway Lists and DNS policies.

## Local Development

To run locally instead of Railway:

```bash
# Install dependencies
pip install -r requirements.txt

# Set up credentials
cp .env.example .env
# Edit .env with your credentials

# Run manually
python3 generate-lists.py
python3 upload_to_cloudflare.py
```

## Files

```
.
├── railway.json              # Railway deployment config
├── start.sh                  # Cron job entry point
├── generate-lists.py         # Downloads and generates CSV lists
├── upload_to_cloudflare.py   # Uploads lists via Cloudflare API
├── requirements.txt          # Python dependencies
├── .env.example              # Credentials template (for local dev)
└── README.md                 # This file
```

## Resources

- [Railway Cron Jobs Documentation](https://docs.railway.app/reference/cron-jobs)
- [Cloudflare Zero Trust Docs](https://developers.cloudflare.com/cloudflare-one/)
- [AdGuard DNS Filter](https://github.com/AdguardTeam/FiltersRegistry)

## License

MIT License - see [LICENSE](LICENSE) file.

AdGuard DNS Filter has its own license - see [AdGuard Filters Repository](https://github.com/AdguardTeam/AdguardFilters).
