#!/usr/bin/env bash
# Shared helpers for the scripts/live/*.sh suite: black-box tests that run
# against the real deployed instance over HTTPS. No secrets are hardcoded
# here -- SOMBA_BASE_URL/SSH_HOST are overridable via env for use against any
# environment, not just the one VPS.
set -euo pipefail

SOMBA_BASE_URL="${SOMBA_BASE_URL:-https://somba.ddns.net}"
SSH_HOST="${SSH_HOST:-kodedlabs}"
COMPOSE_DIR="${COMPOSE_DIR:-/home/kodedlabs/somba}"

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
info() { printf '\033[36m==> %s\033[0m\n' "$1"; }

summary() {
    echo
    printf 'Results: %d passed, %d failed\n' "$PASS" "$FAIL"
    [ "$FAIL" -eq 0 ]
}

# assert_eq <actual> <expected> <description>
assert_eq() {
    if [ "$1" = "$2" ]; then
        pass "$3 (got $1)"
    else
        fail "$3 (expected $2, got $1)"
    fi
}

# json_get <json> <python-expr-on-'d'>  -- e.g. json_get "$body" "d['plan']['id']"
json_get() {
    python3 -c "import sys, json; d = json.load(sys.stdin); print($2)" <<<"$1"
}

# curl_json <method> <path> <auth-header-or-empty> <idem-key-or-empty> <json-body-or-empty>
# Prints "<status>\n<body>"
curl_json() {
    local method="$1" path="$2" auth="$3" idem="$4" body="$5"
    local args=(-sS -m 20 -o /tmp/somba_live_resp.$$ -w '%{http_code}' -X "$method" "$SOMBA_BASE_URL$path" -H "Content-Type: application/json")
    [ -n "$auth" ] && args+=(-H "Authorization: Bearer $auth")
    [ -n "$idem" ] && args+=(-H "Idempotency-Key: $idem")
    [ -n "$body" ] && args+=(-d "$body")
    local status
    status=$(curl "${args[@]}")
    echo "$status"
    cat /tmp/somba_live_resp.$$
    rm -f /tmp/somba_live_resp.$$
}

# Runs a Python one-liner inside the deployed app container. Used ONLY for
# steps that have no public API and cannot be produced organically against
# LIVE Nomba without a human completing real bank verification (setting a
# mandate_id, or forcing a specific Nomba response deterministically). Same
# technique as the pytest suite's monkeypatch, aimed at the real deployment
# instead of local SQLite -- clearly logged wherever it's used.
remote_py() {
    ssh "$SSH_HOST" "cd '$COMPOSE_DIR' && docker compose exec -T app python -c \"$1\""
}

# The scheduler ticks every 30-60s in the background against the same
# production DB these scripts drive through the public API. For steps that
# need a deterministic outcome (e.g. simulating a specific Nomba response),
# pause it so the real tick doesn't race the simulated call.
scheduler_pause() {
    ssh "$SSH_HOST" "cd '$COMPOSE_DIR' && docker compose stop scheduler" >/dev/null 2>&1
}

scheduler_resume() {
    ssh "$SSH_HOST" "cd '$COMPOSE_DIR' && docker compose start scheduler" >/dev/null 2>&1
}

ensure_webhook_echo() {
    ssh "$SSH_HOST" "docker inspect somba-webhook-echo >/dev/null 2>&1 || docker run -d --name somba-webhook-echo --network somba_default mendhak/http-https-echo:37 >/dev/null"
}

# Sets a customer's mandate_id directly -- the public API deliberately
# doesn't expose this (a real one only comes from completed bank
# verification), so tests that need a "chargeable" customer must set it
# through the real app process against the real DB.
set_customer_mandate() {
    local customer_id="$1" mandate_id="$2"
    ssh "$SSH_HOST" "cd '$COMPOSE_DIR' && docker compose exec -T app python -c \"
from somba.db.session import SessionLocal
from somba.db.models import Customer
db = SessionLocal()
c = db.get(Customer, $customer_id)
c.mandate_id = '$mandate_id'
db.commit()
print('mandate set')
\""
}

new_merchant() {
    local name="$1" webhook_url="${2:-}"
    local resp status body
    resp=$(curl_json POST /v1/merchants "" "new-merchant-$$-$RANDOM" "{\"name\":\"$name\",\"webhook_url\":\"$webhook_url\",\"webhook_secret\":\"live-test-$$\"}")
    status=$(head -1 <<<"$resp")
    body=$(tail -n +2 <<<"$resp")
    if [ "$status" != "201" ]; then
        echo "FATAL: merchant creation failed ($status): $body" >&2
        exit 1
    fi
    echo "$body"
}
