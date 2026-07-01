#!/usr/bin/env bash
# Runs the full live test suite against the deployed instance in sequence.
# Any single script's assertion failures don't stop the others -- we want a
# full picture of what's broken, not a stop at the first red.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

overall_fail=0
for script in 01_smoke_test.sh 02_recovery_test.sh 03_payment_uncertain_test.sh 04_proration_test.sh 05_isolation_test.sh; do
    echo
    echo "########################################################################"
    echo "# $script"
    echo "########################################################################"
    if ! bash "./$script"; then
        overall_fail=1
    fi
done

echo
if [ "$overall_fail" -eq 0 ]; then
    echo "ALL SCRIPTS PASSED"
else
    echo "ONE OR MORE SCRIPTS HAD FAILURES -- see output above"
fi
exit "$overall_fail"
