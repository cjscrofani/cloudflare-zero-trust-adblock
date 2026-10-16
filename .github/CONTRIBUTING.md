# Contributing

Thanks for taking an interest. This is a small project, so the process is short.

## Reporting problems

Open an issue using the bug report template. Include the script output with your account ID redacted. Never paste an API token.

## Proposing changes

1. Fork the repository and create a branch.
2. Make your change. Keep the scripts dependency-light; `requests` and `python-dotenv` are the only runtime dependencies.
3. Run both scripts locally:

   ```bash
   python3 generate-lists.py
   python3 upload_to_cloudflare.py --dry-run
   ```

4. If you changed behavior or flags, update the README.
5. Open a pull request. The CI workflow will run the generator against the live AdGuard filter on Python 3.8 and 3.12.

## Ideas that would be welcome

- Updating the existing DNS policy in place instead of creating a new one on each run
- Support for additional blocklist formats (hosts file, plain domain list)
- An allowlist file that is excluded from the generated lists
- Tests for the AdGuard parser

## Code style

Plain Python 3.8-compatible code, no type-checking or formatter requirements. Match the style of the surrounding code.
