# Quickstart: Personal API Key (GUI and cURL)

This document helps you quickly understand and use a Personal API Key ("API Key") to call APIs that require an authenticated user identity.

## 1. Prerequisites and key points

1. You need a VaultSage account and must be able to sign in to VaultSage before you can create a Personal API Key.
2. An API Key is an alternative to `Authorization: Bearer ...` for authentication.
3. A Personal API Key is sent via the HTTP header `X-Api-Key`.
4. The plaintext `api_key` is returned only once at creation time. Save it immediately.

## 2. When to use Bearer vs API Key

1. Use a Bearer token when:
   1. You need to create/list/revoke Personal API Keys (API key management endpoints).
   2. You are logging in or doing a full interactive user flow.
2. Use a Personal API Key when:
   1. You want to call normal user endpoints (for example, `GET /users/me`).
   2. You want a quick script/tool-based verification without handling login flows repeatedly.

## 3. Two ways to obtain/manage an API Key (GUI or API)

### 3.1 Option A: Use the VaultSage GUI

1. Sign in to VaultSage.
2. Go to Settings -> API Keys: `https://vaultsage.ai/settings?tab=api-keys`.
3. Create a Personal API Key.
4. Copy and securely store the plaintext `api_key` (it is usually shown only once).
5. To revoke/delete the key, return to the same page and revoke/delete it.

### 3.2 Option B: Use the API (good for scripts/automation)

This is a pure API flow: use a Bearer token to create an API key, then use `X-Api-Key` to call normal user endpoints.

## 4. Optional: run the test script

If you want an automated end-to-end verification (login -> create key -> call with key -> forbidden checks -> revoke -> verify revoked), you can run:

1. `personal_api_key_quickstart_test.sh` (in this folder)

It will prompt for email/password if you do not export them as environment variables.

```bash
chmod +x personal_api_key_quickstart_test.sh
./personal_api_key_quickstart_test.sh
```

## 5. Environment variables (for the API flow)

```bash
export API_BASE="https://api.vaultsage.ai/api/v1"

# Option A: obtain a Bearer token via login API
export TEST_USER_EMAIL="<your_email>"
export TEST_USER_PASSWORD="<your_password>"

# Option B: if you already captured a Bearer token from browser DevTools
export ACCESS_TOKEN="<existing_access_token>"
```

If you do not have `ACCESS_TOKEN` yet, use Option A (curl only) and copy the `access_token` from the response:

```bash
curl -sS -X POST "$API_BASE/login/access-token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=$TEST_USER_EMAIL" \
  --data-urlencode "password=$TEST_USER_PASSWORD"
```

Then set it manually:

```bash
export ACCESS_TOKEN="<paste_access_token_here>"
```

## 6. Quickstart (API create key -> use key -> revoke key)

### 6.1 Verify your Bearer token works

```bash
curl -sS "$API_BASE/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.2 Create a Personal API Key

```bash
curl -sS -X POST "$API_BASE/users/me/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Copy `key_id` and `api_key` from the response and export them:

```bash
export PERSONAL_KEY_ID="<paste_key_id_here>"
export PERSONAL_API_KEY="<paste_api_key_here>"
```

### 6.3 Call a normal user endpoint using `X-Api-Key`

```bash
curl -sS "$API_BASE/users/me" \
  -H "X-Api-Key: $PERSONAL_API_KEY"
```

### 6.4 Revoke the API Key

```bash
curl -sS -X DELETE "$API_BASE/users/me/api-keys/$PERSONAL_KEY_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 6.5 Verify a revoked key can no longer be used

```bash
curl -sS -i "$API_BASE/users/me" \
  -H "X-Api-Key: $PERSONAL_API_KEY"
```

Expected: HTTP `401` with error code `API_KEY_DELETED`.

## 7. Common restrictions and errors

### 7.1 A Personal API Key cannot manage API keys

Calling `/users/me/api-keys*` with `X-Api-Key` should be forbidden:

```bash
curl -sS -i "$API_BASE/users/me/api-keys" \
  -H "X-Api-Key: $PERSONAL_API_KEY"
```

Expected: HTTP `403` with error code `API_KEY_ENDPOINT_FORBIDDEN`.

### 7.2 A Personal API Key cannot call team management endpoints

```bash
curl -sS -i "$API_BASE/team" \
  -H "X-Api-Key: $PERSONAL_API_KEY"
```

Expected: HTTP `403` with error code `API_KEY_ENDPOINT_FORBIDDEN`.

### 7.3 Do not send both `X-Api-Key` and `X-Team-Api-Key`

```bash
curl -sS -i "$API_BASE/users/me" \
  -H "X-Api-Key: $PERSONAL_API_KEY" \
  -H "X-Team-Api-Key: dummy-team-key"
```

Expected: HTTP `422` with error code `API_KEY_HEADER_CONFLICT`.

## 8. Security notes (minimum)

1. Do not commit `PERSONAL_API_KEY` to git, and do not paste it into issues/PRs/chats.
2. Do not ship an API key in a frontend bundle.
3. Revoke keys when you are done (see Section 6.4).

## 9. Endpoints used in this guide (no source code required)

1. Obtain Bearer token: `POST /api/v1/login/access-token`
2. Get current user: `GET /api/v1/users/me`
   1. Header (choose one): `Authorization: Bearer <token>` or `X-Api-Key: <api_key>`
3. Create Personal API Key: `POST /api/v1/users/me/api-keys`
   1. Header: `Authorization: Bearer <token>`
4. Revoke Personal API Key: `DELETE /api/v1/users/me/api-keys/{key_id}`
   1. Header: `Authorization: Bearer <token>`
