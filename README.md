# Network-wide ad blocking with Cloudflare Zero Trust

[![CI](https://github.com/cjscrofani/cloudflare-zero-trust-adblock/actions/workflows/ci.yml/badge.svg)](https://github.com/cjscrofani/cloudflare-zero-trust-adblock/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Last commit](https://img.shields.io/github/last-commit/cjscrofani/cloudflare-zero-trust-adblock)](https://github.com/cjscrofani/cloudflare-zero-trust-adblock/commits/main)
[![GitHub stars](https://img.shields.io/github/stars/cjscrofani/cloudflare-zero-trust-adblock?style=flat)](https://github.com/cjscrofani/cloudflare-zero-trust-adblock/stargazers)

Block ads, trackers, and malicious domains on every device, on every network, using [Cloudflare Zero Trust](https://www.cloudflare.com/zero-trust/) Gateway as a DNS filter. This project takes the [AdGuard DNS filter](https://github.com/AdguardTeam/FiltersRegistry) (roughly 185,000 domains), splits it into Cloudflare Gateway lists, and uploads them behind a **single** DNS block policy via the API.

It is a free, hardware-free alternative to running a Pi-hole, AdGuard Home, or paying for NextDNS. Cloudflare's free Zero Trust plan covers up to 50 users, and the [WARP client](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/) or [DNS-over-HTTPS](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/agentless/dns/) extends protection to phones and laptops away from home.

> **Warning:** The AdGuard DNS filter is aggressive. Some sites and apps will break. Test in a controlled environment before rolling it out to a whole household or team.

## Table of contents

- [Features](#features)
- [How it compares](#how-it-compares)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Automated updates with GitHub Actions](#automated-updates-with-github-actions)
- [Automated updates with cron](#automated-updates-with-cron)
- [Configuration](#configuration)
- [Manual upload](#manual-upload)
- [How it works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [Command reference](#command-reference)
- [Cloudflare reference](#cloudflare-reference)
- [Security notes](#security-notes)
- [Contributing](#contributing)
- [License](#license)

## Features

- **~185K domains and ~70 IPs** from the AdGuard DNS filter, refreshed on every run
- **One DNS policy** instead of hundreds of regex rules
- **Fully automated deployment** through the Cloudflare API, with an interactive mode and a non-interactive mode for schedulers
- **Dry run** flag to validate credentials before touching your account
- **GitHub Actions workflow** included, so updates can run weekly with no server of your own
- Domains and IPs are separated automatically into the correct Gateway list types
- Tuned for the Standard plan limit of 1,000 entries per list, with a one-line switch for Enterprise
- Works with any AdGuard-formatted filter list, not just the default

## How it compares

| | This project | [cloudflare-gateway-pihole-scripts](https://github.com/mrrfv/cloudflare-gateway-pihole-scripts) | Pi-hole / AdGuard Home | NextDNS |
|---|---|---|---|---|
| Language | Python | JavaScript / Node | Any (self-hosted) | Hosted |
| Hardware needed | None | None | Yes | None |
| Default blocklist | AdGuard DNS filter | Configurable (several) | Configurable | Built-in |
| Policies created | 1 | 1 or more | n/a | n/a |
| Protects devices off-network | Yes, via WARP or DoH | Yes, via WARP or DoH | Only with a VPN | Yes |
| Cost | Free (Cloudflare free plan) | Free | Hardware + power | Free tier, then paid |

Pick this project if you want a minimal Python tool that does one thing: keep the AdGuard DNS filter deployed to your Cloudflare account.

## Requirements

- Python 3.8 or newer
- A [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) account. The free plan works.
- A Cloudflare API token with Zero Trust edit permissions (instructions below)

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/cjscrofani/cloudflare-zero-trust-adblock.git
cd cloudflare-zero-trust-adblock
pip install -r requirements.txt
```

### 2. Add your Cloudflare credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_API_TOKEN=your-api-token
```

Where to find them:

- **Account ID:** Cloudflare dashboard, then Zero Trust, then Settings
- **API token:** Cloudflare dashboard, then My Profile, then API Tokens, then Create Token. Use the **Edit Cloudflare Zero Trust** template.

### 3. Generate the lists

```bash
python3 generate-lists.py
```

This downloads the current AdGuard DNS filter, strips it down to plain domains and IPs, and writes one CSV per 1,000 entries into the `lists/` folder. Expect around 185 domain files and 1 IP file.

### 4. Upload to Cloudflare

Check credentials first without changing anything:

```bash
python3 upload_to_cloudflare.py --dry-run
```

Then deploy:

```bash
python3 upload_to_cloudflare.py
```

The script creates the Gateway lists, uploads every entry, creates a DNS policy named **Block AdGuard DNS Filter** that references all of them, and enables it. On later runs it offers to delete the previous AdGuard lists first.

### 5. Point your devices at Cloudflare

Blocking only applies to DNS traffic that reaches your Gateway. The simplest options:

- Install the [WARP client](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/warp/deployment/manual-deployment/) and enroll in your Zero Trust organization
- Use your Gateway [DNS-over-HTTPS endpoint](https://developers.cloudflare.com/cloudflare-one/connections/connect-devices/agentless/dns/) in a browser or OS that supports it
- Set your Gateway IPv6 or DoH location on a router

## Automated updates with GitHub Actions

The repository ships with a workflow at `.github/workflows/update-blocklist.yml` that regenerates and re-uploads the lists every Sunday at 02:00 UTC, and can be triggered by hand from the Actions tab. No server required.

1. **Fork** this repository.
2. In your fork, go to **Settings**, then **Secrets and variables**, then **Actions**, and add two repository secrets:
   - `CLOUDFLARE_ACCOUNT_ID`
   - `CLOUDFLARE_API_TOKEN`
3. Go to the **Actions** tab and enable workflows for the fork.
4. Open **Update blocklist** and click **Run workflow** to do the first deployment.

The workflow runs `generate-lists.py` and then `upload_to_cloudflare.py --auto-approve`, which deletes the old AdGuard lists and replaces them. Because the lists are replaced rather than edited, there is a short window during each run where the policy references lists that no longer exist. Schedule it for a quiet hour.

## Automated updates with cron

If you would rather run it on a machine you control:

```bash
crontab -e
```

Add a line like this, adjusting the paths:

```cron
0 2 * * 0 cd /path/to/cloudflare-zero-trust-adblock && /usr/bin/python3 generate-lists.py && /usr/bin/python3 upload_to_cloudflare.py --auto-approve >> /var/log/adguard-update.log 2>&1
```

Use `which python3` to find the interpreter path. The `--auto-approve` flag (or `-y`) skips every prompt.

## Configuration

### Enterprise plan

Enterprise accounts allow 5,000 entries per list. Change line 20 of `generate-lists.py`:

```python
MAX_DOMAINS_PER_LIST = 5000
```

This cuts the list count from roughly 185 to roughly 37.

### Custom filter source

Any AdGuard-syntax filter works, from a URL or a local file:

```bash
python3 generate-lists.py https://example.com/custom-filter.txt
python3 generate-lists.py ./local-filter.txt
```

Only plain `||domain.com^` rules are kept. Rules with paths, modifiers, or wildcards are skipped because Gateway lists do not support them.

## Manual upload

If you prefer not to use the API:

1. Run `python3 generate-lists.py` to create the CSV files.
2. In Zero Trust, go to **My Team**, then **Lists**, and click **Upload CSV**.
3. For each `lists/adguard_domains_*.csv`, choose list type **Hostname** and name it "AdGuard Domains - Part N".
4. For `lists/adguard_ips_1.csv`, choose list type **IP** and name it "AdGuard IPs".
5. Go to **Gateway**, then **Firewall Policies**, then **DNS**, and add a policy named "Block AdGuard DNS Filter" with every list joined by OR and the action set to **Block**.

## How it works

1. `generate-lists.py` downloads the filter, parses each `||domain^` line, discards anything Gateway lists cannot express, deduplicates, and splits the result into CSVs of at most 1,000 entries.
2. `upload_to_cloudflare.py` creates one Gateway list per CSV (type `DOMAIN` for hostnames, type `IP` for addresses), appends the entries, then creates one DNS policy whose traffic expression ORs every list together:

```text
any(dns.domains[*] in $list_1) or any(dns.domains[*] in $list_2) or ... or any(dns.resolved_ips[*] in $ip_list_1)
```

### Why Gateway lists instead of regex policies?

| Approach | Policies needed | Maintenance |
|---|---|---|
| Gateway lists (this project) | 1 | Re-run the script |
| Regex patterns | ~500 | Painful |

A regex generator is still included for reference. `python3 domain-lists-dc.py` writes `blocklist_*.txt` files that fit Cloudflare's 6,500-character limit per DNS policy. You would need to create one policy per file by hand, so the lists method is strongly recommended.

### Repository layout

```text
.
├── generate-lists.py            Download the filter and write CSV lists
├── upload_to_cloudflare.py      Create Gateway lists and the DNS policy via API
├── domain-lists-dc.py           Alternative regex generator (not recommended)
├── requirements.txt             Python dependencies
├── .env.example                 Credentials template
├── .github/workflows/           CI and scheduled update workflows
└── lists/                       Generated CSV files (gitignored)
```

## Troubleshooting

**`No module named 'requests'`**
Run `pip install -r requirements.txt`.

**`No CSV files found`**
Run `python3 generate-lists.py` before the upload script.

**`Missing Cloudflare credentials`**
Copy `.env.example` to `.env` and fill in real values. In GitHub Actions, check that both secrets are set on the fork, not the upstream repo.

**`invalid list type`**
Gateway's API expects `DOMAIN` for hostnames and `IP` for addresses. The upload script sets these correctly. If you edited the script, check the `list_type` arguments.

**`list has type IP but should have type Host`**
A `dns.domains[*]` selector was used with an IP list. IP lists need `dns.resolved_ips[*]`. The upload script handles this.

**`cannot have list with over 1000 items`**
You are on the Standard plan. Keep `MAX_DOMAINS_PER_LIST = 1000`.

**`A resource with this identifier already exists`**
Lists from a previous run are still present. Gateway will not delete a list while a policy references it, so the upload script deletes the existing **Block AdGuard DNS Filter** policy first, then the lists. Re-run the script and answer yes to both delete prompts, or pass `--auto-approve`. If a list still fails to delete, the script now prints the API response so you can see why.

**A site I need is blocked**
Create a second DNS policy in Zero Trust with action **Allow** for that domain and place it above the block policy. Policies are evaluated top to bottom.

## Command reference

```bash
# Generate lists from the default AdGuard DNS filter
python3 generate-lists.py

# Generate lists from a custom source
python3 generate-lists.py https://example.com/filter.txt
python3 generate-lists.py ./local-filter.txt

# Upload interactively
python3 upload_to_cloudflare.py

# Upload without prompts (cron, CI)
python3 upload_to_cloudflare.py --auto-approve
python3 upload_to_cloudflare.py -y

# Validate credentials only
python3 upload_to_cloudflare.py --dry-run

# Help
python3 upload_to_cloudflare.py --help
```

## Cloudflare reference

### Gateway list types

| Dashboard name | API type | Used for |
|---|---|---|
| Hostname | `DOMAIN` | Domain blocking |
| IP | `IP` | IP blocking |
| URL | `URL` | URL filtering |
| Email | `EMAIL` | Email filtering |

The dashboard says "Hostname" but the API wants `DOMAIN`. Sending `HOSTNAME` returns `invalid list type`.

### List limits

| Plan | Entries per list | Max file size |
|---|---|---|
| Standard | 1,000 | 2 MB |
| Enterprise | 5,000 | 2 MB |

### DNS policy selectors

```text
any(dns.domains[*] in $list_id)        # domain lists
any(dns.resolved_ips[*] in $list_id)   # IP lists
```

### Documentation

- [Cloudflare Zero Trust](https://developers.cloudflare.com/cloudflare-one/)
- [Gateway lists](https://developers.cloudflare.com/cloudflare-one/policies/gateway/lists/)
- [DNS policies](https://developers.cloudflare.com/cloudflare-one/policies/gateway/dns-policies/)
- [Gateway rules API](https://developers.cloudflare.com/api/resources/zero_trust/subresources/gateway/subresources/rules/)
- [AdGuard DNS filter](https://github.com/AdguardTeam/FiltersRegistry)

## Security notes

- `.env` is gitignored. Never commit it.
- Scope the API token to Zero Trust only. The **Edit Cloudflare Zero Trust** template is sufficient.
- In GitHub Actions, credentials live in repository secrets and are never written to the log.
- All generated files (`lists/`, `filter.txt`, `blocklist_*.txt`) are gitignored.
- See [SECURITY.md](.github/SECURITY.md) for how to report a vulnerability.

## Contributing

Bug reports, filter suggestions, and pull requests are welcome. See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for the short version of how to get started.

## License

MIT. See [LICENSE](LICENSE).

The AdGuard DNS filter is maintained by AdGuard and distributed under its own terms. See the [AdGuard filters repository](https://github.com/AdguardTeam/AdguardFilters).

## Disclaimer

Use at your own risk. Blocking this many domains will affect some websites and apps. Test before deploying to people who depend on the network.

## Credits

- The AdGuard team for maintaining the DNS filter
- Cloudflare for Zero Trust Gateway
