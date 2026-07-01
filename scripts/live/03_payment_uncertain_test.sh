#!/usr/bin/env bash
# payment_uncertain path: a charge attempt Nomba can't confirm (e.g. a
# timeout) must park the subscription, not lose or double-charge it, then
# the verify pass resolves it once Nomba's definitive status is known.
#
# The specific Nomba outcomes (uncertain, then confirmed success) are
# simulated for the same reason as the other live scripts: there's no way to
# make a real timeout happen on demand against LIVE. Everything else --
# state transitions, ledger status, invoice, healing -- is real.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./common.sh

info "03: payment_uncertain test (timeout -> freeze -> verify -> resolves)"

MERCHANT=$(new_merchant "Uncertain Test $$" "")
API_KEY=$(json_get "$MERCHANT" "d['api_key']")

scheduler_pause
trap scheduler_resume EXIT

resp=$(curl_json POST /v1/plans "$API_KEY" "unc-plan-$$" '{"name":"Uncertain Plan","amount":6000,"interval":"month","currency":"NGN"}')
PLAN_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")

resp=$(curl_json POST /v1/customers "$API_KEY" "unc-cust-$$" '{"email":"uncertain+'"$$"'@test.com","name":"Uncertain Customer"}')
CUST_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['customer']['id']")
set_customer_mandate "$CUST_ID" "mandate-uncertain-sim" >/dev/null

resp=$(curl_json POST /v1/subscriptions "$API_KEY" "unc-sub-$$" "{\"customer_id\":$CUST_ID,\"plan_id\":$PLAN_ID}")
SUB_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['id']")

info "simulating a Nomba timeout on the charge attempt (status=uncertain)"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.charge.worker import run, execute_pending
from unittest.mock import patch
from somba.nomba.client import NombaChargeResult, NombaChargeStatus

def fake_debit(**kwargs):
    return NombaChargeResult(status=NombaChargeStatus.uncertain, transaction_id=None, failure_reason='network_error: timeout', response_code=None)

db = SessionLocal()
written = run(db)
with patch('somba.nomba.client.debit_mandate', side_effect=fake_debit):
    processed = execute_pending(db)
print('written', written, 'processed', processed)
db.close()
" > /tmp/somba_unc_charge.$$ 2>&1
cat /tmp/somba_unc_charge.$$
grep -q "written 1" /tmp/somba_unc_charge.$$ && pass "billing sweep wrote this subscription's intent" || fail "billing sweep wrote this subscription's intent"
rm -f /tmp/somba_unc_charge.$$

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "payment_uncertain" "subscription frozen at payment_uncertain, not lost or double-charged"

resp=$(curl_json GET "/v1/metrics" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['metrics']['pending_intents']")" "1" "ledger intent still pending (RPO=0 -- nothing silently dropped)"

info "verify pass: Nomba now confirms the debit actually went through"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.reconcile import verify_pass
from unittest.mock import patch
from somba.nomba.client import NombaChargeResult, NombaChargeStatus

def fake_verify(**kwargs):
    # transaction_id must be unique per attempt: write_settlement treats a
    # repeated transaction_ref as a duplicate and skips healing, so a fixed
    # string here would only ever heal the very first run that used it.
    return NombaChargeResult(status=NombaChargeStatus.succeeded, transaction_id='sim-verify-' + kwargs.get('order_reference', ''), failure_reason=None, response_code='00')

db = SessionLocal()
with patch('somba.nomba.client.verify_transaction', side_effect=fake_verify):
    resolved = verify_pass.run(db)
print('resolved', resolved)
db.close()
" > /tmp/somba_unc_verify.$$ 2>&1
cat /tmp/somba_unc_verify.$$
grep -qE "resolved [1-9]" /tmp/somba_unc_verify.$$ && pass "verify pass resolved at least this uncertain attempt" || fail "verify pass resolved at least this uncertain attempt"
rm -f /tmp/somba_unc_verify.$$

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "active" "subscription resolved to active"

resp=$(curl_json GET "/v1/metrics" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['metrics']['pending_intents']")" "0" "no more pending intents"
assert_eq "$(json_get "$body" "d['metrics']['payment_uncertain_subscriptions']")" "0" "no subscriptions stuck in payment_uncertain"

scheduler_resume
trap - EXIT
summary