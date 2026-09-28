"""Local test: exercise the streamable-http transport (remote deploy path)."""
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8124/mcp"


async def main() -> int:
    async with streamable_http_client(URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = sorted(t.name for t in tools.tools)
            assert len(names) == 4, names
            print("TOOLS over HTTP:", names)

            r = await session.call_tool("get_pricing", {})
            d = json.loads(r.content[0].text)
            assert d["products"][1]["price_usd"] == 3
            print("get_pricing over HTTP OK")

            r = await session.call_tool(
                "get_free_questions", {"exam": "CCNA", "count": 3}
            )
            d = json.loads(r.content[0].text)
            assert d["returned"] == 3 and d["exam"] == "Cisco CCNA (200-301)", d["exam"]
            assert "bytebarhq.com" in d["attribution"]
            print("get_free_questions over HTTP OK:", d["returned"], "for", d["exam"])

    print("ALL HTTP TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
