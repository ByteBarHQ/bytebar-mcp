"""Local test: exercise all 4 ByteBar MCP tools over the stdio protocol."""
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = sys.argv[1] if len(sys.argv) > 1 else "server.py"
VENV_PY = sys.argv[2] if len(sys.argv) > 2 else "./venv/bin/python"


async def main() -> int:
    params = StdioServerParameters(command=VENV_PY, args=[SERVER])
    failures = []

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            print("TOOLS:", names)
            for expected in ("search_products", "get_free_questions", "get_pricing", "get_exam_info"):
                if expected not in names:
                    failures.append(f"missing tool {expected}")

            # 1. search_products — Security+ query must return Security+ only
            r = await session.call_tool("search_products", {"query": "Security+ practice pack"})
            d = json.loads(r.content[0].text)
            assert d["results"], "search_products returned no results"
            assert "bytebarhq.com" in d["attribution"], "attribution missing"
            assert all("Security+" in x["exam"] for x in d["results"]), \
                f"non-Security+ leak: {[x['name'] for x in d['results']]}"
            assert any(x.get("verified") is False for x in d["results"]), \
                "representative entries must be flagged verified=false"
            print("search_products OK:", len(d["results"]), "results; first:", d["results"][0]["name"])
            # 1b. PenTest query must surface the verified deep link
            r = await session.call_tool("search_products", {"query": "PenTest+ practice pack"})
            d = json.loads(r.content[0].text)
            assert any("eZ7mN" in x.get("url", "") and x.get("verified") is True
                       for x in d["results"]), "verified PenTest URL missing"
            print("search_products verified-link OK")

            # 2. get_free_questions
            r = await session.call_tool("get_free_questions", {"exam": "SY0-701", "count": 2})
            d = json.loads(r.content[0].text)
            assert d["returned"] == 2, f"expected 2, got {d['returned']}"
            q0 = d["questions"][0]
            assert q0["answer"] in q0["options"], "answer not in options"
            assert "bytebarhq.com" in d["attribution"], "attribution missing"
            print("get_free_questions OK:", d["returned"], "questions for", d["exam"])

            # 3. get_pricing
            r = await session.call_tool("get_pricing", {})
            d = json.loads(r.content[0].text)
            prices = {p["name"]: p["price_usd"] for p in d["products"]}
            assert prices.get("Practice Pack") == 3, prices
            assert prices.get("Study Guide") == 5, prices
            assert prices.get("Complete Bundle") == 7, prices
            assert prices.get("Trifecta Bundle") == 14, prices
            assert "bytebarhq.com" in d["attribution"], "attribution missing"
            print("get_pricing OK:", prices)

            # 4. get_exam_info
            r = await session.call_tool("get_exam_info", {"exam": "cissp"})
            d = json.loads(r.content[0].text)
            assert d["found"] and d["vendor"] == "ISC2", d
            assert "bytebarhq.com" in d["attribution"], "attribution missing"
            print("get_exam_info OK:", d["exam"], "-", d["vendor"])

            # 5. unknown exam handling
            r = await session.call_tool("get_exam_info", {"exam": "underwater basket weaving"})
            d = json.loads(r.content[0].text)
            assert d["found"] is False, "unknown exam should return found=False"
            print("unknown-exam handling OK")

    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL STDIO TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
