/**
 * Build-time env (Vite): set in `frontend/.env.local` or shell when running `npm run dev` / `npm run build`.
 * Matches `PERSONAL_API_KEY` + header `X-Api-Key` from nurie_api_doc/curl_personal_api_key_verification.md.
 */

export const DEFAULT_NURIE_API_BASE = 'https://api.vault.nurie.ai'

export function getViteNurieApiKey() {
  return String(import.meta.env.VITE_NURIE_API_KEY || '').trim()
}

export function getViteNurieApiBase() {
  return String(import.meta.env.VITE_NURIE_API_BASE || '').trim()
}

/** Backend that proxies Nurie (FastAPI in this repo). */
export function getViteBackendUrl() {
  return String(import.meta.env.VITE_BACKEND_URL || '').trim()
}
