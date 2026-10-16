# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-10-16

First tagged release.

### Added

- `generate-lists.py`: downloads the AdGuard DNS filter and splits it into Gateway-compatible CSV lists, separating domains from IPs
- `upload_to_cloudflare.py`: creates Gateway lists and a single DNS block policy via the Cloudflare API, with `--dry-run` and `--auto-approve` modes
- `domain-lists-dc.py`: legacy regex generator for the policy-per-file approach
- GitHub Actions workflow for weekly automated updates using repository secrets
- CI workflow that validates the generator against the live filter on Python 3.8 and 3.12
- Issue and pull request templates, contributing guide, and security policy

[1.0.0]: https://github.com/cjscrofani/cloudflare-zero-trust-adblock/releases/tag/v1.0.0
