# Security policy

## Scope

This project handles a Cloudflare API token with permission to edit Zero Trust settings. Issues that could leak that token, or that could cause the scripts to modify resources outside the AdGuard lists and policy they manage, are in scope.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private vulnerability reporting on this repository's **Security** tab, or email the maintainer through the address on their GitHub profile.

You should hear back within a week. Fixes will be published as a new release with a note in the changelog.

## Good practice for users

- Create the API token from the **Edit Cloudflare Zero Trust** template rather than a global API key.
- Store the token in `.env` locally or in GitHub Actions repository secrets. Never commit it.
- Review the workflow file before enabling it on a fork.
