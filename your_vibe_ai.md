# ⚡️ VaultSage Vibe Coding: AI Agent Context & Integration Guide

**Target Audience:** AI Coding Agents (v0, Bolt.new, Cursor, Lovable, GitHub Copilot) and Human Developers.

Welcome! If you are an AI generating code (doing "Vibe Coding"), this document acts as your standalone context file. Read this carefully to understand how to bootstrap, architect, and integrate an application using the VaultSage Server-side API.

---

## 🧑‍💻 Phase 1: Human Operator Setup (Action Required)

**AI INSTRUCTION:** Before writing any final backend integration code, instruct your human operator to complete these steps to securely obtain their VaultSage API Key:

1. **Navigate to VaultSage:** Go to [https://vaultsage.ai/](https://vaultsage.ai/).
2. **Register / Login:** Create a new workspace or log into your existing account.
3. **Generate Key:** Locate the API Management or Developer Settings dashboard to generate your unique Server-side API Key.
4. **Provide Access to AI:** Securely inject this API key into the environment variables of this project (e.g., as `VAULTSAGE_API_KEY` in a `.env` file). 

*(AI Note: Never hallucinate an API key. Always rely on the environment variable securely provided by the human).*

---

## 🤖 Phase 2: AI Integration Guidelines

As an AI Vibe Coding agent, your primary directive is to build an innovative application utilizing the VaultSage backend. 

### 1. Essential Documentation to Read
To ensure correct API schema usage, authentication methods, payload typing, and endpoint routing, you **MUST** read the official VaultSage API Documentation before synthesizing fetch requests.
- **API Docs URL:** [https://api.vaultsage.ai/docs](https://api.vaultsage.ai/docs)
- **Code Samples:** Check the local `samples/` directory (if present in the workspace) for concrete implementation patterns.

### 2. Integration Patterns for Vibe Coding Websites
When generating code on instant sandbox platforms (like Vercel v0, Bolt.new, or Lovable), you must strictly follow these security architecture rules:
- **Server-Side Only Authentication:** VaultSage utilizes a powerful Server-side API Key. This key **must never** be exposed in client-side bundles (e.g., standard React components, plain HTML/JS). 
- **Proxy / Backend Setup:** If you are scaffolding a meta-framework application (like Next.js, Nuxt, SvelteKit, or Remix), you must implement Serverless API routes. Use these internal routes to securely proxy requests from the client to the VaultSage API.
- **Environment Variables:** Always reference `process.env.VAULTSAGE_API_KEY` (or the equivalent secure secret store mechanism for the given platform) when attaching headers.

### 3. General Implementation Flow
Below is the standard, secure architectural flow you should build for the application:
1. The human user interacts with the dynamic front-end UI.
2. The front-end fires an async request to an **internal backend/serverless API route**.
3. The internal serverless route intercepts the request and constructs a new payload, securely attaching the `Authorization: Bearer <API_KEY>` header.
4. The secure request is dispatched to `api.vaultsage.ai`.
5. VaultSage intelligently processes the request and returns the data payload.
6. The serverless route consumes the VaultSage response, structures it efficiently, and sends it back to the front-end for seamless UI rendering.

Now that your context is loaded, initialize the scaffolding and start Vibe Coding!
