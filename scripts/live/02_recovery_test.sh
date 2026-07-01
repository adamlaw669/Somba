#!/usr/bin/env bash
# Recovery path: force a "risk"-classified failure -> transfer path selected
# -> a real Nomba virtual account is issued -> simulate a push transfer
# landing on it -> reconciliation heals the subscription back to active.
#
# The failure classification and VA issuance are REAL (real Nomba API call,
# real DB writes). Only the initial debit_mandate response is simulated,
# for the same reason as the smoke test: forcing a specific outcome (a
# fraud/risk decline) on demand against LIVE Nomba isn't something that can
# be produced organically. The "push transfer" is simulated the same way a
# real transfer would arrive -- as a settlement matched by virtual account
# number, run through the real write_settlement healing path.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./common.sh

info "02: recovery test (force failure -> VA issued -> simulate push -> reconcile -> active)"

MERCHANT=$(new_merchant "Recovery Test $$" "")
API_KEY=$(json_get "$MERCHANT" "d['api_key']")
MERCHANT_ID=$(json_get "$MERCHANT" "d['merchant']['id']")

scheduler_pause
trap scheduler_resume EXIT

resp=$(curl_json POST /v1/plans "$API_KEY" "rec-plan-$$" '{"name":"Recovery Plan","amount":8000,"interval":"month","currency":"NGN"}')
PLAN_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")

resp=$(curl_json POST /v1/customers "$API_KEY" "rec-cust-$$" '{"email":"recovery+'"$$"'@test.com","name":"Recovery Customer"}')
CUST_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['customer']['id']")
set_customer_mandate "$CUST_ID" "mandate-recovery-sim" >/dev/null

resp=$(curl_json POST /v1/subscriptions "$API_KEY" "rec-sub-$$" "{\"customer_id\":$CUST_ID,\"plan_id\":$PLAN_ID}")
SUB_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['id']")

info "forcing a risk-classified decline (response_code=34) -> should select the transfer path"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.charge.worker import run, execute_pending
from unittest.mock import patch
from somba.nomba.client import NombaChargeResult, NombaChargeStatus

def fake_debit(**kwargs):
    return NombaChargeResult(status=NombaChargeStatus.failed, transaction_id=None, failure_reason='suspected fraud', response_code='34')

db = SessionLocal()
written = run(db)
with patch('somba.nomba.client.debit_mandate', side_effect=fake_debit):
    processed = execute_pending(db)
print('written', written, 'processed', processed)
db.close()
" > /tmp/somba_rec_charge.$$ 2>&1
cat /tmp/somba_rec_charge.$$
grep -q "written 1" /tmp/somba_rec_charge.$$ && pass "billing sweep wrote this subscription's intent" || fail "billing sweep wrote this subscription's intent"
rm -f /tmp/somba_rec_charge.$$

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "past_due" "subscription moved to past_due on failure"

info "checking transfer_required event carries a real, freshly-issued virtual account"
resp=$(curl_json GET "/v1/events?event_type=subscription.transfer_required" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
n=$(json_get "$body" "len(d['events'])")
assert_eq "$n" "1" "exactly one transfer_required event"
FAILURE_CLASS=$(json_get "$body" "d['events'][0]['payload']['failure_class']")
assert_eq "$FAILURE_CLASS" "risk" "classified as risk (response_code=34)"
VA_NUMBER=$(json_get "$body" "d['events'][0]['payload'].get('virtual_account',{}).get('account_number','')")
if [ -n "$VA_NUMBER" ]; then
    pass "virtual account issued in transfer_required payload: $VA_NUMBER"
else
    fail "virtual account issued in transfer_required payload"
fi

resp=$(curl_json GET "/v1/customers/$CUST_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['customer']['va_account_no']")" "$VA_NUMBER" "customer record has the same VA number persisted"

info "simulating a push transfer landing on that VA, then reconciling"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.reconcile.writer import write_settlement
from somba.db.models import LedgerSettlementSource

db = SessionLocal()
payload = {'data': {'transaction': {'destinationAccountNumber': '$VA_NUMBER', 'transactionId': 'sim-push-$$', 'transactionAmount': 80.0}}}
res = write_settlement(
    db, merchant_id=$MERCHANT_ID, order_reference='', transaction_ref='sim-push-$$',
    amount_kobo=8000, source=LedgerSettlementSource.transfer_push, raw_payload=payload,
)
db.commit()
print('healed', res.healed, 'status', res.status.value)
db.close()
" > /tmp/somba_rec_heal.$$ 2>&1
cat /tmp/somba_rec_heal.$$
grep -q "healed True" /tmp/somba_rec_heal.$$ && pass "push transfer matched and healed via VA" || fail "push transfer matched and healed via VA"
rm -f /tmp/somba_rec_heal.$$

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['status']")" "active" "subscription recovered to active after reconciliation"

scheduler_resume
trap - EXIT
summary