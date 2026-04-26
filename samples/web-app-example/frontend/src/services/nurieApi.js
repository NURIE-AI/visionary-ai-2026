const API_PREFIX = '/api/v1'
export const BACKEND_VAULT_PREFIX = '/nurie/vault'

export function normalizeBase(base) {
  if (base === undefined || base === null) return ''
  return String(base).trim().replace(/\/$/, '')
}

/**
 * @param {string} base - Absolute origin or '' for same-origin paths
 * @param {string} path - Must start with /
 */
export function buildUrl(base, path) {
  const b = normalizeBase(base)
  const p = path.startsWith('/') ? path : `/${path}`
  if (!b) return p
  return `${b}${p}`
}

export function authHeadersFromConfig({ authMode, apiKey, bearerToken }) {
  if (authMode === 'bearer' && bearerToken) {
    return { Authorization: `Bearer ${bearerToken.trim()}` }
  }
  if (apiKey) {
    return { 'X-Api-Key': apiKey.trim() }
  }
  return {}
}

/**
 * @param {object} opts
 * @param {'backend'|'direct'} opts.transport
 * @param {string} opts.backendOrigin - '' for same-origin `/nurie/...` (Vite proxy)
 * @param {string} opts.directBase - Nurie API origin when transport is direct
 * @param {Record<string, string>} opts.authHeaders - Nurie auth; only for direct
 * @param {File[]} opts.files
 * @param {{ conflictResolution?: string, directoryId?: string }} [opts.uploadOpts]
 */
export async function uploadFiles(opts) {
  const {
    transport,
    backendOrigin,
    directBase,
    authHeaders,
    files,
    conflictResolution = 'keep',
    directoryId,
  } = opts

  const params = new URLSearchParams({ conflict_resolution: conflictResolution })
  if (directoryId) params.set('directory_id', directoryId)

  let url
  let headers = {}
  if (transport === 'backend') {
    url = buildUrl(
      normalizeBase(backendOrigin),
      `${BACKEND_VAULT_PREFIX}/files/?${params.toString()}`,
    )
  } else {
    url = buildUrl(
      normalizeBase(directBase),
      `${API_PREFIX}/files/?${params.toString()}`,
    )
    headers = { ...authHeaders }
  }

  const body = new FormData()
  for (const f of files) {
    body.append('files', f)
  }

  const res = await fetch(url, { method: 'POST', headers, body })
  const data = await readJsonSafe(res)
  return { res, data }
}

/**
 * @param {object} opts
 * @param {'backend'|'direct'} opts.transport
 * @param {string} opts.backendOrigin
 * @param {string} opts.directBase
 * @param {Record<string, string>} opts.authHeaders
 * @param {object} opts.payload
 */
export async function postChatV2(opts) {
  const { transport, backendOrigin, directBase, authHeaders, payload } = opts

  let url
  let headers = { 'Content-Type': 'application/json' }
  if (transport === 'backend') {
    url = buildUrl(normalizeBase(backendOrigin), `${BACKEND_VAULT_PREFIX}/chat/message/v2`)
  } else {
    url = buildUrl(normalizeBase(directBase), `${API_PREFIX}/chat/message/v2`)
    headers = { ...headers, ...authHeaders }
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  })
  const data = await readJsonSafe(res)
  return { res, data }
}

export async function fetchVaultProxyStatus(backendOrigin) {
  const url = buildUrl(normalizeBase(backendOrigin), `${BACKEND_VAULT_PREFIX}/status`)
  const res = await fetch(url)
  const data = await readJsonSafe(res)
  return { res, data }
}

async function readJsonSafe(res) {
  const text = await res.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return { _raw: text }
  }
}

export function formatApiError(data) {
  if (!data) return 'Unknown error'
  if (typeof data === 'string') return data
  if (data.detail) {
    const d = data.detail
    if (typeof d === 'string') return d
    if (Array.isArray(d)) {
      return d.map((x) => x.msg || JSON.stringify(x)).join('; ')
    }
    if (typeof d === 'object' && d.message) return String(d.message)
    return JSON.stringify(d)
  }
  if (data.message) return String(data.message)
  if (data._raw) return data._raw
  return JSON.stringify(data)
}
