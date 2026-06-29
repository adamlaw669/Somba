# Deployment

This page explains how Somba should be deployed to a VPS and what URL Nomba should call for inbound webhooks. It also outlines the GitHub Actions flow for CI and automatic deployment.

## Deployment goal

The goal is simple: every push to the main branch should pass checks, then deploy to the VPS without a manual copy-paste step.

## Public webhook URL

Nomba should send inbound events to:

`https://<your-domain>/v1/webhooks/nomba`

That is the webhook URL for the project. The actual domain depends on the VPS and DNS setup, but the path should stay the same.

## GitHub Actions flow

The repository should use two workflows:

- A CI workflow that checks formatting, importability, and basic validation
- A deploy workflow that syncs the code to the VPS and restarts the app

The deployment uses the repository `Dockerfile` and `docker-compose.yml`, so the VPS only needs Docker and Docker Compose installed.

## Secrets and variables

Use repository secrets for sensitive values such as:

- VPS host
- VPS username
- SSH private key

Use repository variables for non-sensitive values such as:

- App deploy path
- Public base URL
- Service name

Recommended variable names:

- `VPS_APP_DIR`
- `PUBLIC_BASE_URL`
- `SERVICE_NAME`

## VPS responsibilities

The VPS should:

- Run the app
- Expose the public domain over HTTPS
- Allow the webhook endpoint to be reached from Nomba
- Restart cleanly after a deploy

## Rollout notes

The first deployment should be treated as a setup step, not a full production launch. After the app is live, test the webhook URL with a known event and verify the response path end to end.
