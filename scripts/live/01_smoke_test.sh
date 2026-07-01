#!/usr/bin/env bash
# Golden path against the live deployment:
#   create merchant -> plan -> customer -> subscribe -> bill -> charge ->
#   webhook delivered -> subscription shows active.
#
# The billing sweep and Nomba call run for real, over the wire, through the
# actually-deployed code. The one exception: a successful direct debit needs
# a REAL completed bank mandate, which needs a human to finish bank
# verification -- there is no way to automate that. So the debit_mandate
# response itself is simulated (same technique as the pytest suite's
# monkeypatch, aimed at the live deployment); everything else -- intent
# writing, invoice, state machine, webhook signing and delivery -- is the
# real deployed code running against the real deployed DB.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./common.sh

info "01: smoke test (create -> bill -> charge -> webhook -> active)"

ensure_webhook_echo

MERCHANT=$(new_merchant "Smoke Test $$" "http://somba-webhook-echo:8080/smoke")
API_KEY=$(json_get "$MERCHANT" "d['api_key']")
info "merchant created, api_key=${API_KEY:0:12}..."

scheduler_pause
trap scheduler_resume EXIT

resp=$(curl_json POST /v1/plans "$API_KEY" "smoke-plan-$$" '{"name":"Smoke Plan","amount":5000,"interval":"month","currency":"NGN"}')
status=$(head -1 <<<"$resp"); body=$(tail -n +2 <<<"$resp")
assert_eq "$status" "201" "create plan"
PLAN_ID=$(json_get "$body" "d['plan']['id']")

resp=$(curl_json POST /v1/customers "$API_KEY" "smoke-cust-$$" '{"email":"smoke+'"$$"'@test.com","name":"Smoke Customer"}')
status=$(head -1 <<<"$resp"); body=$(tail -n +2 <<<"$resp")
assert_eq "$status" "201" "create customer"
CUST_ID=$(json_get "$body" "d['customer']['id']")

set_customer_mandate "$CUST_ID" "mandate-smoke-sim" >/dev/null

resp=$(curl_json POST /v1/subscriptions "$API_KEY" "smoke-sub-$$" "{\"customer_id\":$CUST_ID,\"plan_id\":$PLAN_ID}")
status=$(head -1 <<<"$resp"); body=$(tail -n +2 <<<"$resp")
assert_eq "$status" "201" "create subscription"
SUB_ID=$(json_get "$body" "d['subscription']['id']")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "active" "subscription starts active (no trial)"

info "billing: writing intent (real) then simulating a successful Nomba debit"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.charge.worker import run, execute_pending
from unittest.mock import patch
from somba.nomba.client import NombaChargeResult, NombaChargeStatus

def fake_debit(**kwargs):
    return NombaChargeResult(status=NombaChargeStatus.succeeded, transaction_id='sim-smoke-txn', failure_reason=None, response_code='00')

db = SessionLocal()
written = run(db)
with patch('somba.nomba.client.debit_mandate', side_effect=fake_debit):
    processed = execute_pending(db)
print('written', written, 'processed', processed)
db.close()
" > /tmp/somba_smoke_charge.$$ 2>&1
cat /tmp/somba_smoke_charge.$$
grep -q "written 1" /tmp/somba_smoke_charge.$$ && pass "billing sweep wrote this subscription's intent" || fail "billing sweep wrote this subscription's intent"
rm -f /tmp/somba_smoke_charge.$$

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
status=$(head -1 <<<"$resp"); body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "active" "subscription is active after successful charge"

resp=$(curl_json GET "/v1/invoices" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['invoices'][0]['status']")" "paid" "invoice marked paid"

scheduler_resume
trap - EXIT
info "webhook emitter runs on its own 30s tick — waiting for delivery"
s=""
for _ in $(seq 1 20); do
    resp=$(curl_json GET "/v1/events?event_type=charge.succeeded" "$API_KEY" "" "")
    body=$(tail -n +2 <<<"$resp")
    n=$(json_get "$body" "len(d['events'])")
    if [ "$n" != "0" ]; then
        s=$(json_get "$body" "d['events'][0]['status']")
        [ "$s" = "published" ] && break
    fi
    sleep 3
done
assert_eq "$s" "published" "charge.succeeded webhook delivered to merchant (gym app's source of truth for 'active')"

summary