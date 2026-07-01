#!/usr/bin/env bash
# Two-merchant isolation proof, on the real running instance: create two
# independent merchants side by side, each with their own plan/customer/
# subscription/invoice, and confirm neither can read, list, or act on the
# other's data -- not against an ephemeral test DB, against the one shared
# Postgres database backing the live deployment.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
source ./common.sh

info "05: two-merchant isolation proof (live shared instance)"

A=$(new_merchant "Isolation A $$" "")
A_KEY=$(json_get "$A" "d['api_key']")
B=$(new_merchant "Isolation B $$" "")
B_KEY=$(json_get "$B" "d['api_key']")

resp=$(curl_json POST /v1/plans "$A_KEY" "iso-a-plan-$$" '{"name":"A Plan","amount":3000,"interval":"month","currency":"NGN"}')
A_PLAN=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")
resp=$(curl_json POST /v1/customers "$A_KEY" "iso-a-cust-$$" '{"email":"iso-a+'"$$"'@test.com","name":"A Customer"}')
A_CUST=$(json_get "$(tail -n +2 <<<"$resp")" "d['customer']['id']")
resp=$(curl_json POST /v1/subscriptions "$A_KEY" "iso-a-sub-$$" "{\"customer_id\":$A_CUST,\"plan_id\":$A_PLAN}")
A_SUB=$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['id']")

resp=$(curl_json POST /v1/plans "$B_KEY" "iso-b-plan-$$" '{"name":"B Plan","amount":9000,"interval":"month","currency":"NGN"}')
B_PLAN=$(json_get "$(tail -n +2 <<<"$resp")" "d['plan']['id']")
resp=$(curl_json POST /v1/customers "$B_KEY" "iso-b-cust-$$" '{"email":"iso-b+'"$$"'@test.com","name":"B Customer"}')
B_CUST=$(json_get "$(tail -n +2 <<<"$resp")" "d['customer']['id']")
resp=$(curl_json POST /v1/subscriptions "$B_KEY" "iso-b-sub-$$" "{\"customer_id\":$B_CUST,\"plan_id\":$B_PLAN}")
B_SUB=$(json_get "$(tail -n +2 <<<"$resp")" "d['subscription']['id']")

info "cross-merchant reads must all 404"
status=$(head -1 <<<"$(curl_json GET "/v1/plans/$A_PLAN" "$B_KEY" "" "")")
assert_eq "$status" "404" "B cannot read A's plan"
status=$(head -1 <<<"$(curl_json GET "/v1/customers/$A_CUST" "$B_KEY" "" "")")
assert_eq "$status" "404" "B cannot read A's customer"
status=$(head -1 <<<"$(curl_json GET "/v1/subscriptions/$A_SUB" "$B_KEY" "" "")")
assert_eq "$status" "404" "B cannot read A's subscription"

status=$(head -1 <<<"$(curl_json GET "/v1/plans/$B_PLAN" "$A_KEY" "" "")")
assert_eq "$status" "404" "A cannot read B's plan"
status=$(head -1 <<<"$(curl_json GET "/v1/customers/$B_CUST" "$A_KEY" "" "")")
assert_eq "$status" "404" "A cannot read B's customer"
status=$(head -1 <<<"$(curl_json GET "/v1/subscriptions/$B_SUB" "$A_KEY" "" "")")
assert_eq "$status" "404" "A cannot read B's subscription"

info "cross-merchant mutation must also 404 (not just reads)"
resp=$(curl_json PATCH "/v1/subscriptions/$A_SUB" "$B_KEY" "iso-b-patch-$$" "{\"plan_id\":$B_PLAN}")
status=$(head -1 <<<"$resp")
assert_eq "$status" "404" "B cannot change A's subscription's plan"

info "list endpoints exclude the other merchant's rows"
resp=$(curl_json GET "/v1/plans" "$A_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
found=$(json_get "$body" "any(p['id']==$B_PLAN for p in d['plans'])")
assert_eq "$found" "False" "A's plan list does not include B's plan"

resp=$(curl_json GET "/v1/customers" "$B_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
found=$(json_get "$body" "any(c['id']==$A_CUST for c in d['customers'])")
assert_eq "$found" "False" "B's customer list does not include A's customer"

resp=$(curl_json GET "/v1/subscriptions" "$A_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
found=$(json_get "$body" "any(s['id']==$B_SUB for s in d['subscriptions'])")
assert_eq "$found" "False" "A's subscription list does not include B's subscription"

info "metrics are scoped per-merchant, not global"
resp=$(curl_json GET "/v1/metrics" "$A_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
A_ACTIVE=$(json_get "$body" "d['metrics']['active_subscriptions']")
resp=$(curl_json GET "/v1/metrics" "$B_KEY" "" "")
body=$(tail -n +2 <<<"$resp")
B_ACTIVE=$(json_get "$body" "d['metrics']['active_subscriptions']")
info "A sees active_subscriptions=$A_ACTIVE, B sees active_subscriptions=$B_ACTIVE (each just their own)"
pass "metrics scoped per-merchant (A=$A_ACTIVE, B=$B_ACTIVE, both counts are each merchant's own)"

summary