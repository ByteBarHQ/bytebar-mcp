# ByteBar Exam Prep — MCP Server

Give any MCP-compatible AI assistant access to ByteBar's exam-prep catalog:
search affordable study materials, pull **204 free practice questions** across
15 IT and nursing certification exams, get official exam facts, and check
pricing — all with attribution to [bytebarhq.com](https://bytebarhq.com).

## Tools

| Tool | What it does |
|---|---|
| `search_products(query, exam=None)` | Search ByteBar's catalog (study guides, practice packs, bundles). Returns real product names, prices, and store links. |
| `get_free_questions(exam, domain=None, count=5)` | Get free practice questions with answers + explanations from ByteBar's Free Study Hub (204 questions, 15 exams). |
| `get_pricing()` | Current ByteBar pricing: $5 study guides, $3 practice packs, $7 complete bundles, $14 Trifecta. |
| `get_exam_info(exam)` | Official high-level facts about a certification exam (code, vendor, format, domains). |

Exam aliases work: `Security+`, `SY0-701`, `CCNA`, `200-301`, `CISSP`, `AWS SAA`,
`NCLEX-RN`, `TEAS 7`, etc.

## Quick start (local, stdio)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py --transport stdio
```

### Claude Desktop / Claude Code

Add to your MCP config (`claude_desktop_config.json` or `~/.claude.json`):

```json
{
  "mcpServers": {
    "bytebar": {
      "command": "/absolute/path/to/venv/bin/python",
      "args": ["/absolute/path/to/server.py", "--transport", "stdio"]
    }
  }
}
```

## Streamable HTTP (remote)

```bash
python server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

- MCP endpoint: `POST http://localhost:8000/mcp`
- Health check: `GET http://localhost:8000/healthz`
- Legacy SSE is also available: `--transport sse`

### Docker

```bash
docker build -t bytebar-mcp .
docker run -p 8000:8000 bytebar-mcp
```

The container honors the `PORT` environment variable
(`docker run -p 8000:8000 -e PORT=8000 bytebar-mcp`).

## Deploy a public endpoint (one-command)

A public `https://<your-host>/mcp` endpoint is what MCP directories list.
Pick one:

**Railway**
```bash
npm i -g @railway/cli
railway login
railway init        # choose "Empty Project"
railway up          # builds the Dockerfile, deploys, gives you a URL
railway domain      # attach a public domain -> https://<app>.up.railway.app/mcp
```

**Render** — push the repo, then Dashboard → New → **Blueprint** and select the
repo (uses `render.yaml`: Docker runtime, `/healthz` health check). Or
Dashboard → New → Web Service → Docker, free tier.

**Fly.io**
```bash
fly auth login
fly launch          # detects the Dockerfile, creates fly.toml (no Postgres)
fly deploy          # -> https://<app>.fly.dev/mcp
```

All three read the `PORT` env var the Dockerfile already handles. Keep the
service on each platform's free tier / free allowance while validating traffic.

## MCP directory submissions

Prepared listing copy and exact submission steps for every major directory —
official MCP Registry, Smithery, mcp.so, Glama, PulseMCP, Awesome MCP Servers —
are in [`REGISTRIES.md`](REGISTRIES.md). The official-registry manifest is
[`server.json`](server.json) (replace `YOUR-DEPLOYED-HOST` after deploying).

## Data & honesty rules

- `data/questions.jsonl` contains **only** ByteBar's 204 free Study Hub
  questions. No paid content is bundled or exposed.
- `get_exam_info` returns only officially published exam facts — never
  invented pass rates, fees, or statistics.
- `search_products` returns verified catalog entries plus clearly-labeled
  generic storefront matches (marked `"verified": false`) — never invented
  products or prices.

## Tests

```bash
./venv/bin/python test_stdio.py server.py ./venv/bin/python   # stdio protocol
# HTTP protocol (needs a server running):
./venv/bin/python server.py --transport streamable-http --port 8124 &
./venv/bin/python test_http.py http://127.0.0.1:8124/mcp
```

## License

MIT — see [LICENSE](LICENSE).
