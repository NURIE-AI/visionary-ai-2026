#!/usr/bin/env bash

set -euo pipefail

# Quickstart test runner for Personal API Key flow.
#
# Usage:
#   1) Option A (recommended): export env vars then run
#        export TEST_USER_EMAIL="you@example.com"
#        export TEST_USER_PASSWORD="your-password"
#        ./personal_api_key_quickstart_test.sh
#   2) Option B: run and input when prompted
#
# Notes:
# - This script targets the public environment by default.
# - It stops at the first unexpected response.

API_BASE="${API_BASE:-https://api.vaultsage.ai/api/v1}"
TEST_USER_EMAIL="${TEST_USER_EMAIL:-}"
TEST_USER_PASSWORD="${TEST_USER_PASSWORD:-}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 2
  fi
}

json_get() {
  local key="$1"
  local file="$2"

  if command -v jq >/dev/null 2>&1; then
    jq -r "$key" "$file"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    python3 - "$key" "$file" <<'PY'
import json
import sys

key = sys.argv[1]
path = sys.argv[2]

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def get(obj, dotted):
    cur = obj
    for part in dotted.strip('.').split('.'):
        if part == '':
            continue
        cur = cur[part]
    return cur

val = get(data, key)
if val is None:
    print("null")
else:
    print(val)
PY
    return 0
  fi

  echo "Need jq or python3 to parse JSON." >&2
  exit 2
}

curl_with_status() {
  local method="$1"
  local url="$2"
  local out_body="$3"
  shift 3

  # shellcheck disable=SC2086
  curl -sS -X "$method" "$url" \
    -o "$out_body" \
    -w "%{http_code}" \
    "$@"
}

expect_status() {
  local got="$1"
  local want="$2"
  local body_file="$3"
  local label="$4"

  if [[ "$got" != "$want" ]]; then
    echo "[$label] Unexpected HTTP status: got=$got want=$want" >&2
    echo "[$label] Response body:" >&2
    cat "$body_file" >&2
    exit 1
  fi
}

expect_status_one_of() {
  local got="$1"
  local want_a="$2"
  local want_b="$3"
  local body_file="$4"
  local label="$5"

  if [[ "$got" != "$want_a" && "$got" != "$want_b" ]]; then
    echo "[$label] Unexpected HTTP status: got=$got want=$want_a|$want_b" >&2
    echo "[$label] Response body:" >&2
    cat "$body_file" >&2
    exit 1
  fi
}

expect_body_contains() {
  local body_file="$1"
  local needle="$2"
  local label="$3"

  if command -v rg >/dev/null 2>&1; then
    if rg -q --fixed-strings "$needle" "$body_file"; then
      return 0
    fi
  else
    if grep -Fq -- "$needle" "$body_file"; then
      return 0
    fi
  fi

    echo "[$label] Expected response body to contain: $needle" >&2
    echo "[$label] Response body:" >&2
    cat "$body_file" >&2
    exit 1
}

main() {
  need_cmd curl

  if [[ -z "$TEST_USER_EMAIL" ]]; then
    read -r -p "VaultSage email: " TEST_USER_EMAIL
  fi

  if [[ -z "$TEST_USER_PASSWORD" ]]; then
    read -r -s -p "VaultSage password (hidden): " TEST_USER_PASSWORD
    echo
  fi

  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  echo "API_BASE=$API_BASE"

  # 1) Login: POST /login/access-token
  local login_body="$tmpdir/login.json"
  local login_code
  login_code="$(curl_with_status "POST" "$API_BASE/login/access-token" "$login_body" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=$TEST_USER_EMAIL" \
    --data-urlencode "password=$TEST_USER_PASSWORD")"

  expect_status "$login_code" "200" "$login_body" "login"
  local access_token
  access_token="$(json_get '.access_token' "$login_body")"
  if [[ -z "$access_token" || "$access_token" == "null" ]]; then
    echo "[login] Missing access_token in response" >&2
    echo "[login] Response body:" >&2
    cat "$login_body" >&2
    exit 1
  fi
  echo "[login] OK"

  # 2) GET /users/me with Bearer
  local me_bearer_body="$tmpdir/me_bearer.json"
  local me_bearer_code
  me_bearer_code="$(curl_with_status "GET" "$API_BASE/users/me" "$me_bearer_body" \
    -H "Authorization: Bearer $access_token")"
  expect_status "$me_bearer_code" "200" "$me_bearer_body" "users_me_bearer"
  local my_id
  my_id="$(json_get '.id' "$me_bearer_body")"
  echo "[users/me bearer] OK (id=$my_id)"

  # 3) POST /users/me/api-keys
  local create_body="$tmpdir/create_key.json"
  local create_code
  create_code="$(curl_with_status "POST" "$API_BASE/users/me/api-keys" "$create_body" \
    -H "Authorization: Bearer $access_token")"
  expect_status "$create_code" "200" "$create_body" "create_key"
  local key_id
  local api_key
  key_id="$(json_get '.key_id' "$create_body")"
  api_key="$(json_get '.api_key' "$create_body")"
  if [[ -z "$key_id" || "$key_id" == "null" || -z "$api_key" || "$api_key" == "null" ]]; then
    echo "[create_key] Missing key_id/api_key in response" >&2
    echo "[create_key] Response body:" >&2
    cat "$create_body" >&2
    exit 1
  fi
  echo "[create_key] OK (key_id=$key_id)"

  # 4) GET /users/me with X-Api-Key
  local me_key_body="$tmpdir/me_key.json"
  local me_key_code
  me_key_code="$(curl_with_status "GET" "$API_BASE/users/me" "$me_key_body" \
    -H "X-Api-Key: $api_key")"
  expect_status "$me_key_code" "200" "$me_key_body" "users_me_api_key"
  local my_id2
  my_id2="$(json_get '.id' "$me_key_body")"
  if [[ "$my_id" != "null" && "$my_id2" != "null" && "$my_id" != "$my_id2" ]]; then
    echo "[users/me api key] Unexpected user id mismatch: bearer=$my_id api_key=$my_id2" >&2
    echo "[users/me api key] Response body:" >&2
    cat "$me_key_body" >&2
    exit 1
  fi
  echo "[users/me api key] OK"

  # 5) Forbidden: API key cannot call /users/me/api-keys
  local forbidden_self_body="$tmpdir/forbidden_self.txt"
  local forbidden_self_code
  forbidden_self_code="$(curl_with_status "GET" "$API_BASE/users/me/api-keys" "$forbidden_self_body" \
    -H "X-Api-Key: $api_key")"
  expect_status "$forbidden_self_code" "403" "$forbidden_self_body" "forbidden_self_crud"
  expect_body_contains "$forbidden_self_body" "API_KEY_ENDPOINT_FORBIDDEN" "forbidden_self_crud"
  echo "[forbidden self-crud] OK"

  # 6) Forbidden: API key cannot call team management
  local forbidden_team_body="$tmpdir/forbidden_team.txt"
  local forbidden_team_code
  forbidden_team_code="$(curl_with_status "GET" "$API_BASE/team" "$forbidden_team_body" \
    -H "X-Api-Key: $api_key")"
  expect_status "$forbidden_team_code" "403" "$forbidden_team_body" "forbidden_team"
  expect_body_contains "$forbidden_team_body" "API_KEY_ENDPOINT_FORBIDDEN" "forbidden_team"
  echo "[forbidden team] OK"

  # 7) Header conflict
  local conflict_body="$tmpdir/header_conflict.txt"
  local conflict_code
  conflict_code="$(curl_with_status "GET" "$API_BASE/users/me" "$conflict_body" \
    -H "X-Api-Key: $api_key" \
    -H "X-Team-Api-Key: dummy-team-key")"
  expect_status "$conflict_code" "422" "$conflict_body" "header_conflict"
  expect_body_contains "$conflict_body" "API_KEY_HEADER_CONFLICT" "header_conflict"
  echo "[header conflict] OK"

  # 8) Revoke key
  local revoke_body="$tmpdir/revoke.json"
  local revoke_code
  revoke_code="$(curl_with_status "DELETE" "$API_BASE/users/me/api-keys/$key_id" "$revoke_body" \
    -H "Authorization: Bearer $access_token")"
  expect_status_one_of "$revoke_code" "200" "204" "$revoke_body" "revoke_key"
  echo "[revoke] OK"

  # 9) Using revoked key should be 401
  local deleted_body="$tmpdir/deleted.txt"
  local deleted_code
  deleted_code="$(curl_with_status "GET" "$API_BASE/users/me" "$deleted_body" \
    -H "X-Api-Key: $api_key")"
  expect_status "$deleted_code" "401" "$deleted_body" "use_deleted_key"
  expect_body_contains "$deleted_body" "API_KEY_DELETED" "use_deleted_key"
  echo "[use deleted key] OK"

  echo "All checks passed."
}

main "$@"
