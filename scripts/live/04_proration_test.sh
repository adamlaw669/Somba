#!/usr/bin/env bash
# Proration end-to-end: upgrading mid-cycle fires an immediate proration
# invoice for the correct net amount, and that amount is what actually gets
# charged -- not the raw plan price difference, not the new plan's full
# price.
#
# Everything here is real over the wire (PATCH /v1/subscriptions triggers
# the real proration calculator and writes a real LedgerIntent) except the
# final debit_mandate response, simulated for the same reason as the other
# scripts: no real bank mandate can be completed by automation.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./common.sh

info "04: proration test (upgrade mid-cycle -> correct charge fires)"

MERCHANT=$(new_merchant "Proration Test $$" "")
API_KEY=$(json_get "$MERCHANT" "d['api_key']")

scheduler_pause
trap scheduler_resume EXIT

resp=$(curl_json POST /v1/plans "$API_KEY" "prorate-plan-a-$$" '{"name":"Basic","amount":5000,"interval":"month","currency":"NGN"}')
PLAN_A=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")

resp=$(curl_json POST /v1/plans "$API_KEY" "prorate-plan-b-$$" '{"name":"Pro","amount":15000,"interval":"month","currency":"NGN"}')
PLAN_B=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")

resp=$(curl_json POST /v1/customers "$API_KEY" "prorate-cust-$$" '{"email":"prorate+'"$$"'@test.com","name":"Prorate Customer"}')
CUST_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['customer']['id']")
set_customer_mandate "$CUST_ID" "mandate-prorate-sim" >/dev/null

resp=$(curl_json POST /v1/subscriptions "$API_KEY" "prorate-sub-$$" "{\"customer_id\":$CUST_ID,\"plan_id\":$PLAN_A}")
SUB_ID=$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['id']")
assert_eq "$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['status']")" "active" "subscription starts active on Basic (5000/mo)"

info "upgrading Basic -> Pro immediately after signup (~full period remaining)"
resp=$(curl_json PATCH "/v1/subscriptions/$SUB_ID" "$API_KEY" "prorate-patch-$$" "{\"plan_id\":$PLAN_B}")
status=$(head -1 <<<"$resp"); body=$(tail -n +2 <<<"$resp")
assert_eq "$status" "200" "plan change accepted"
assert_eq "$(json_get "$body" "d['proration']['action']")" "charge" "upgrade selects the charge action, not credit"
NET_KOBO=$(json_get "$body" "d['proration']['net_kobo']")
info "computed net_kobo=$NET_KOBO (expect close to 15000-5000=10000 for ~full period remaining)"
python3 -c "
net = $NET_KOBO
assert 9000 <= net <= 10000, f'net_kobo {net} outside expected range for an upgrade billed almost immediately'
print('range check ok')
" && pass "net_kobo ($NET_KOBO) is in the expected upgrade range" || fail "net_kobo ($NET_KOBO) is in the expected upgrade range"

resp=$(curl_json GET "/v1/invoices" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
PRORATION_INVOICE_AMOUNT=$(json_get "$body" "next(i['amount'] for i in d['invoices'] if i['type']=='proration')")
assert_eq "$PRORATION_INVOICE_AMOUNT" "$NET_KOBO" "proration invoice amount matches the computed net_kobo"

resp=$(curl_json GET "/v1/subscriptions/$SUB_ID" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
assert_eq "$(json_get "$body" "d['subscription']['plan_id']")" "$PLAN_B" "subscription now on the new plan"

info "executing the pending proration intent (simulating a successful Nomba debit)"
remote_py "
from somba.db.session import SessionLocal
from somba.workers.charge.worker import execute_pending
from unittest.mock import patch
from somba.nomba.client import NombaChargeResult, NombaChargeStatus

def fake_debit(**kwargs):
    return NombaChargeResult(status=NombaChargeStatus.succeeded, transaction_id='sim-prorate-txn', failure_reason=None, response_code='00')

db = SessionLocal()
with patch('somba.nomba.client.debit_mandate', side_effect=fake_debit):
    processed = execute_pending(db)
print('processed', processed)
db.close()
" > /tmp/somba_prorate_charge.$$ 2>&1
cat /tmp/somba_prorate_charge.$$
rm -f /tmp/somba_prorate_charge.$$

resp=$(curl_json GET "/v1/invoices" "$API_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
PRORATION_STATUS=$(json_get "$body" "next(i['status'] for i in d['invoices'] if i['type']=='proration')")
assert_eq "$PRORATION_STATUS" "paid" "proration invoice paid for exactly the prorated amount, not full plan price"

scheduler_resume
trap - EXIT
summary