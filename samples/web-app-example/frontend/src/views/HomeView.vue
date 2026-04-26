<template>
  <div class="nurie-sample">
    <header class="header">
      <h1>Nurie vault sample</h1>
      <p class="lead">
        Upload files and chat with the vault from this page. The UI always calls your
        <strong>FastAPI backend</strong> under <code>/nurie/vault/…</code> so
        <code>NURIE_API_KEY</code> and upstream settings stay in <code>backend/.env</code>, not in
        the browser.
      </p>
      <div class="architecture">
        <h2 class="architecture-title">How it fits together</h2>
        <ol class="architecture-steps">
          <li>
            <strong>Browser (this Vue app)</strong> uses same-origin, relative requests:
            <code>POST /nurie/vault/files/</code> and
            <code>POST /nurie/vault/chat/message/v2</code>. The page never sends a Nurie API key.
          </li>
          <li>
            <strong>Your dev or deploy host</strong> must route <code>/nurie/…</code> to the API
            process. With <code>npm run dev</code>, <strong>Vite</strong> proxies
            <code>/nurie/…</code> to
            <code>VITE_BACKEND_PROXY_TARGET</code> (default
            <code>http://127.0.0.1:8000</code>, see <code>frontend/vite.config.js</code>).
            In production, configure nginx (or your reverse proxy) the same way, or host the static
            files behind the same origin that serves the backend.
          </li>
          <li>
            <strong>FastAPI (this repo’s backend)</strong> implements those routes, attaches
            <code>X-Api-Key: …</code> from <code>NURIE_API_KEY</code>, and calls the real Nurie host
            given by <code>NURIE_API_BASE</code> (plus paths like
            <code>/api/v1/files/</code> and <code>/api/v1/chat/message/v2</code> on the server side).
            See <code>backend/.env.example</code> and the same personal-key story as
            <code>curl_personal_api_key_verification</code> in
            <span class="ref">nurie_api_doc / nurie_ui_sample</span>.
          </li>
        </ol>
        <p class="architecture-foot">
          If uploads or chat fail with a network or CORS error, confirm the backend is running and
          that <code>/nurie</code> reaches it from the same origin the UI uses.
        </p>
      </div>
    </header>

    <section class="card upload-card">
      <h2>Upload file</h2>
      <p class="muted">
        Calls your backend <code>POST /nurie/vault/files/</code> (multipart field
        <code>files</code>), which forwards to Nurie. Uploaded file IDs are attached to the next
        chat messages as context.
      </p>
      <div
        class="drop-zone"
        :class="{ dragover: dragOver, disabled: uploading }"
        @dragenter.prevent="onDragEnter"
        @dragover.prevent="onDragOver"
        @dragleave.prevent="onDragLeave"
        @drop.prevent="onDrop"
        @click="openFilePicker"
      >
        <input
          ref="fileInput"
          type="file"
          class="hidden-input"
          multiple
          @change="onFileInput"
        />
        <template v-if="!uploading">
          <p><strong>Click</strong> or drag files here</p>
          <p class="muted small">Same flow as vault Smart Drop / file APIs in nurie_ui_sample.</p>
        </template>
        <p v-else class="muted">Uploading…</p>
      </div>
      <p v-if="uploadError" class="error">{{ uploadError }}</p>
      <ul v-if="contextualFileIds.length" class="file-list">
        <li v-for="id in contextualFileIds" :key="id">
          <code>{{ id }}</code>
          <button type="button" class="linkish" @click="removeFileId(id)">remove</button>
        </li>
      </ul>
    </section>

    <section class="card chat-card">
      <div class="chat-toolbar">
        <h2>Chat</h2>
        <button type="button" class="btn secondary" :disabled="isSending" @click="newConversation">
          New conversation
        </button>
      </div>
      <p class="muted small">
        Chat v2 via
        <code>POST /nurie/vault/chat/message/v2</code> — first turn sends full transcript; with
        <code>chat_id</code>, only the latest user message (same pattern as
        <span class="ref">nurie_ui_sample</span>).
      </p>
      <div ref="messagesEl" class="messages">
        <div
          v-for="(m, i) in messages"
          :key="i"
          class="bubble"
          :class="m.role"
        >
          <span class="bubble-label">{{ labelFor(m.role) }}</span>
          <div class="bubble-body">{{ m.content }}</div>
        </div>
        <div v-if="isSending" class="bubble assistant pending">Thinking…</div>
      </div>
      <div class="composer">
        <textarea
          v-model="draft"
          rows="2"
          placeholder="Message the vault…"
          :disabled="isSending"
          @keydown.enter.exact.prevent="send"
        />
        <button type="button" class="btn primary" :disabled="isSending || !draft.trim()" @click="send">
          Send
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import { formatApiError, postChatV2, uploadFiles } from '../services/nurieApi.js'

/** Always same-origin paths like `/nurie/vault/...` (Vite or nginx → FastAPI). */
const BACKEND_ORIGIN = ''

export default {
  name: 'HomeView',
  data() {
    return {
      dragOver: false,
      uploading: false,
      uploadError: '',
      contextualFileIds: [],
      messages: [],
      chatId: null,
      draft: '',
      isSending: false,
    }
  },
  methods: {
    pushSystem(text) {
      this.messages.push({ role: 'system', content: text })
      this.$nextTick(() => this.scrollChat())
    },
    labelFor(role) {
      if (role === 'user') return 'You'
      if (role === 'assistant') return 'Vault'
      return 'Note'
    },
    scrollChat() {
      const el = this.$refs.messagesEl
      if (el) el.scrollTop = el.scrollHeight
    },
    openFilePicker() {
      if (this.uploading) return
      this.$refs.fileInput?.click()
    },
    onDragEnter() {
      if (!this.uploading) this.dragOver = true
    },
    onDragOver() {
      if (!this.uploading) this.dragOver = true
    },
    onDragLeave() {
      this.dragOver = false
    },
    onDrop(e) {
      this.dragOver = false
      const files = Array.from(e.dataTransfer?.files || [])
      if (files.length) this.uploadFileList(files)
    },
    onFileInput(e) {
      const files = Array.from(e.target.files || [])
      e.target.value = ''
      if (files.length) this.uploadFileList(files)
    },
    async uploadFileList(files) {
      this.uploadError = ''
      this.uploading = true
      try {
        const { res, data } = await uploadFiles({
          transport: 'backend',
          backendOrigin: BACKEND_ORIGIN,
          directBase: '',
          authHeaders: {},
          files,
          conflictResolution: 'keep',
        })
        if (!res.ok) {
          this.uploadError = formatApiError(data) || res.statusText
          return
        }
        const ids = extractUploadFileIds(data)
        if (!ids.length) {
          this.uploadError = 'Upload succeeded but no file_id was returned.'
          return
        }
        for (const id of ids) {
          if (!this.contextualFileIds.includes(id)) this.contextualFileIds.push(id)
        }
        this.pushSystem(`Uploaded ${ids.length} file(s). IDs added to chat context.`)
      } catch (e) {
        this.uploadError = e instanceof Error ? e.message : String(e)
      } finally {
        this.uploading = false
      }
    },
    removeFileId(id) {
      this.contextualFileIds = this.contextualFileIds.filter((x) => x !== id)
    },
    newConversation() {
      this.chatId = null
      this.messages = []
      this.draft = ''
    },
    toApiMessagesForFullHistory() {
      const fileIds = [...this.contextualFileIds]
      return this.messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m) => ({
          content: m.content,
          actor: m.role === 'user' ? 'user' : 'assistant',
          file_ids: m.role === 'user' && fileIds.length ? fileIds : null,
        }))
    },
    async send() {
      const text = this.draft.trim()
      if (!text || this.isSending) return

      this.draft = ''
      this.messages.push({ role: 'user', content: text })
      this.$nextTick(() => this.scrollChat())

      const contextual =
        this.contextualFileIds.length > 0 ? [...this.contextualFileIds] : null

      let payload
      if (this.chatId) {
        payload = {
          messages: [
            {
              content: text,
              actor: 'user',
              file_ids: contextual || null,
            },
          ],
          contextual_file_ids: contextual,
          chat_id: this.chatId,
          persist: true,
        }
      } else {
        payload = {
          messages: this.toApiMessagesForFullHistory(),
          contextual_file_ids: contextual,
          chat_id: null,
          persist: true,
        }
      }

      this.isSending = true
      try {
        const { res, data } = await postChatV2({
          transport: 'backend',
          backendOrigin: BACKEND_ORIGIN,
          directBase: '',
          authHeaders: {},
          payload,
        })
        if (!res.ok) {
          this.messages.push({
            role: 'system',
            content: `Request failed (${res.status}): ${formatApiError(data)}`,
          })
          return
        }
        const reply =
          data && typeof data.result === 'string' ? data.result : JSON.stringify(data)
        this.messages.push({ role: 'assistant', content: reply })
        if (data && data.new_chat_id) {
          this.chatId = data.new_chat_id
        }
        if (data && Array.isArray(data.suggested_questions) && data.suggested_questions.length) {
          this.messages.push({
            role: 'system',
            content: `Suggested: ${data.suggested_questions.join(' · ')}`,
          })
        }
      } catch (e) {
        this.messages.push({
          role: 'system',
          content: e instanceof Error ? e.message : String(e),
        })
      } finally {
        this.isSending = false
        this.$nextTick(() => this.scrollChat())
      }
    },
  },
}

function extractUploadFileIds(data) {
  if (!data) return []
  if (Array.isArray(data)) {
    return data.map((x) => x && x.file_id).filter(Boolean)
  }
  if (data.file_id) return [data.file_id]
  if (data.files && Array.isArray(data.files)) {
    return data.files.map((x) => x.file_id).filter(Boolean)
  }
  return []
}
</script>

<style scoped>
.nurie-sample {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 16px 48px;
  text-align: left;
}

.header {
  margin-bottom: 24px;
}

.header h1 {
  font-size: 1.5rem;
  margin: 0 0 12px;
  color: #1a2a3a;
  text-align: center;
}

.lead {
  margin: 0 0 16px;
  font-size: 0.95rem;
  color: #334155;
  line-height: 1.55;
  text-align: left;
}

.architecture {
  text-align: left;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px 18px;
}

.architecture-title {
  margin: 0 0 12px;
  font-size: 1.05rem;
  color: #1e293b;
  font-weight: 600;
}

.architecture-steps {
  margin: 0 0 12px;
  padding-left: 1.25rem;
  color: #475569;
  font-size: 0.88rem;
  line-height: 1.55;
}

.architecture-steps li {
  margin-bottom: 10px;
}

.architecture-steps li:last-of-type {
  margin-bottom: 0;
}

.architecture-foot {
  margin: 0;
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.5;
  border-top: 1px solid #e2e8f0;
  padding-top: 12px;
  margin-top: 4px;
}

.ref {
  font-size: inherit;
  color: #64748b;
}

.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.card h2 {
  margin: 0 0 12px;
  font-size: 1.1rem;
  color: #1e293b;
}

.muted {
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.45;
  margin: 0 0 12px;
}

.muted.small {
  font-size: 0.8rem;
}

.drop-zone {
  border: 2px dashed #94a3b8;
  border-radius: 10px;
  padding: 28px 16px;
  text-align: center;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background 0.15s;
}

.drop-zone:hover:not(.disabled),
.drop-zone.dragover {
  border-color: #42b983;
  background: #f0fdf4;
}

.drop-zone.disabled {
  cursor: wait;
  opacity: 0.7;
}

.hidden-input {
  display: none;
}

.error {
  color: #b91c1c;
  font-size: 0.9rem;
  margin-top: 10px;
}

.file-list {
  margin: 12px 0 0;
  padding-left: 18px;
  font-size: 0.85rem;
}

.file-list li {
  margin-bottom: 6px;
}

.linkish {
  margin-left: 8px;
  background: none;
  border: none;
  color: #0ea5e9;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}

.chat-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.chat-toolbar h2 {
  margin: 0;
}

.messages {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  min-height: 220px;
  max-height: 360px;
  overflow-y: auto;
  padding: 12px;
  margin-bottom: 12px;
}

.bubble {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  max-width: 95%;
}

.bubble.user {
  margin-left: auto;
  background: #dbeafe;
  color: #0f172a;
}

.bubble.assistant {
  margin-right: auto;
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #0f172a;
}

.bubble.system {
  margin-left: auto;
  margin-right: auto;
  background: #fef9c3;
  color: #713f12;
  font-size: 0.85rem;
  max-width: 100%;
}

.bubble.pending {
  font-style: italic;
  color: #64748b;
}

.bubble-label {
  display: block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #64748b;
  margin-bottom: 4px;
}

.bubble-body {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.92rem;
  line-height: 1.45;
}

.composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.composer textarea {
  flex: 1;
  resize: vertical;
  min-height: 52px;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-family: inherit;
  font-size: 0.95rem;
}

.btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn.primary {
  background: #42b983;
  color: #fff;
}

.btn.primary:hover:not(:disabled) {
  background: #369f75;
}

.btn.secondary {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

code {
  font-size: 0.85em;
  background: #f1f5f9;
  padding: 1px 5px;
  border-radius: 4px;
}
</style>
