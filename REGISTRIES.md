# ByteBar MCP — Registry Submissions

All submission routes below were verified against the live sites on
September 28, 2026. Submit in this order — the official registry is the
canonical one and several directories auto-ingest from it.

**Prerequisites (do once):** deploy a public endpoint (see `README.md`), push
this repo to GitHub (e.g. `ByteBarHQ/bytebar-mcp`), then in `server.json`
replace `YOUR-DEPLOYED-HOST` with the real host and bump `version` if needed.

## Prepared listing copy (use everywhere)

- **Title:** `ByteBar Exam Prep` (16 chars)
- **Description (directories):**
  `Free IT certification practice questions, exam information, and ByteBar's affordable study materials ($3 practice packs, $5 study guides, $7 bundles) for AI assistants.`
- **Description (official registry, ≤100 chars):**
  `Free IT cert practice questions, exam info, and ByteBar's $3-$7 study materials.`
- **Category:** Education
- **Tags:** `exam-prep, certification, education, practice-questions, comptia, cisco, aws, azure, cybersecurity, nursing, study-tools`
- **Website:** `https://bytebarhq.com`
- **Repository:** `https://github.com/ByteBarHQ/bytebar-mcp`

---

## 1. Official MCP Registry (canonical — do first)

- **URL:** https://registry.modelcontextprotocol.io/
- **How:** CLI publish of `server.json` — no web form, no human review queue.
  Publishing is schema validation + namespace authentication; listings go live
  near-instantly.
- **Steps:**
  ```bash
  npm install -g @modelcontextprotocol/registry-publisher
  mcp-publisher login github     # device flow at github.com/login/device;
                                 # log in as an owner of the ByteBarHQ org
  mcp-publisher publish          # reads ./server.json, validates, uploads
  ```
- **Name:** `io.github.bytebarhq/bytebar-mcp` (already set in `server.json`).
  GitHub auth grants publish rights to the `io.github.bytebarhq/*` namespace.
- **Notes:** description must be ≤100 chars (the API rejects longer with 422).
  `remotes` must be a publicly accessible Streamable HTTP URL ending in `/mcp`.
- **Verify:**
  `curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.bytebarhq/bytebar-mcp"`
- **Why first:** Glama, PulseMCP, the VS Code gallery, and other directories
  auto-ingest from this registry.

## 2. Smithery.ai (largest MCP directory)

- **Submit:** https://smithery.ai/new
- **How:** sign in (GitHub or Google), then add a server by pasting the public
  Streamable HTTP URL (`https://<host>/mcp`) — Smithery auto-scans `tools/list`
  and builds the listing from the repo. Remote servers need no repo re-upload.
- **CLI alternative:**
  ```bash
  npm install -g @smithery/cli
  smithery mcp publish https://<host>/mcp -n bytebarhq/bytebar-mcp
  ```
- **Cost:** listing is free; account sign-in required.
- **Tip:** keep the deployed endpoint online — Smithery re-scans tools
  periodically.

## 3. mcp.so (DR-72 directory)

- **Submit:** https://mcp.so/submit
- **Paid fast-track ($39 one-time, verified live on the submit page):**
  immediate publish without review, verified badge, featured/priority
  placement, dofollow link.
- **Free community route (verified):** comment on the maintainers' submission
  thread — https://github.com/chatmcp/mcpso/issues/1
  ("Submit Your MCP Servers here") — with the server name, URL, and
  description; listings are added after review.
- **Fields:** repository URL, name, description, category.

## 4. Glama (92k+ servers, auto-indexed)

- **Browse:** https://glama.ai/mcp/servers
- **How:** no separate submission needed — Glama indexes the official MCP
  Registry automatically. After step 1, claim/verify the listing by signing in
  to Glama with GitHub.

## 5. PulseMCP (MCP news + directory)

- **Browse:** https://www.pulsemcp.com/
- **How:** auto-ingests from the official MCP Registry; there is also a manual
  submit form on the site. Maintained by a member of the MCP Steering
  Committee who also maintains the official registry, so step 1 covers it.

## 6. Awesome MCP Servers (community list)

- **Repo:** https://github.com/punkpeye/awesome-mcp-servers
- **How:** open a Pull Request adding one line to `README.md` under the
  Education section, per that repo's `CONTRIBUTING.md`.
- **Line:**
  `* [ByteBar Exam Prep](https://github.com/ByteBarHQ/bytebar-mcp) - Free IT certification practice questions, exam info, and affordable ($3-$7) ByteBar study materials for AI assistants.`

---

## Submission checklist

- [ ] Public `https://<host>/mcp` endpoint live (`/healthz` returns ok)
- [ ] GitHub repo public (`ByteBarHQ/bytebar-mcp`)
- [ ] `server.json`: real host in `remotes`, version bumped
- [ ] 1. Official registry published via `mcp-publisher`
- [ ] 2. Smithery submitted
- [ ] 3. mcp.so submitted (paid fast-track or GitHub-issue route)
- [ ] 4. Glama listing claimed
- [ ] 5. PulseMCP confirmed / submitted
- [ ] 6. Awesome MCP Servers PR opened
