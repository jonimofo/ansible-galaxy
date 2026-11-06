#!/usr/bin/env bash
# SPDX-License-Identifier: MIT-0
# Regression test for `make check` (#7): a syntax error must fail the target
# and name the role; a missing tests/test.yml must not. Fixture roles are built
# in a temp directory so no broken role lands in the repo.
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
fixtures=$(mktemp -d)
trap 'rm -rf "$fixtures"' EXIT

mkdir -p "$fixtures/good/tests" "$fixtures/broken/tests" "$fixtures/missing"
printf -- '- hosts: localhost\n  gather_facts: false\n  tasks: []\n' > "$fixtures/good/tests/test.yml"
printf -- '- hosts: localhost\n  tasks: [ broken\n' > "$fixtures/broken/tests/test.yml"

fail() {
    echo "FAIL: $1" >&2
    echo "$2" >&2
    exit 1
}

run_check() {
    make --no-print-directory -C "$repo_root" check CHECK_ROLES="$1" 2>&1
}

if output=$(run_check "$fixtures/good/ $fixtures/missing/"); then
    status=0
else
    status=$?
fi
if [ "$status" -ne 0 ]; then
    fail "make check failed without a broken role (exit $status)" "$output"
fi
if [[ "$output" != *"No test playbook for missing"* ]]; then
    fail "missing tests/test.yml not reported" "$output"
fi

if output=$(run_check "$fixtures/good/ $fixtures/broken/ $fixtures/missing/"); then
    fail "make check passed with a broken tests/test.yml" "$output"
fi
if [[ "$output" != *"Syntax check failed for: broken"* ]]; then
    fail "the failing role is not named" "$output"
fi
if [[ "$output" == *"No test playbook for broken"* ]]; then
    fail "a syntax error is reported as a missing playbook" "$output"
fi

echo "make check regression test: OK"
