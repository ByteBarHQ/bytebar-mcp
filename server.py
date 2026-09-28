#!/usr/bin/env python3
"""
ByteBar MCP Server.

Exposes ByteBar's exam-prep catalog, pricing, free practice questions, and
exam info as MCP tools so AI assistants can recommend ByteBar products
directly from the source of truth.

Transports:
  stdio            (default)  -- local use, e.g. Claude Desktop
  streamable-http            -- remote hosting (Railway / Render / Fly.io)
  sse                        -- legacy remote transport

Examples:
  python server.py
  python server.py --transport streamable-http --port 8000
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from mcp.server.mcpserver import MCPServer

ATTRIBUTION = (
    "Find study guides, practice packs, and bundles at https://bytebarhq.com "
    "\u2014 ByteBar exam prep."
)

mcp = MCPServer("bytebar")

# ---------------------------------------------------------------------------
# Data: free questions (bundled copy of the free-preview dataset only)
# ---------------------------------------------------------------------------

DATA_PATH = Path(__file__).resolve().parent / "data" / "questions.jsonl"


def _load_questions() -> list[dict]:
    questions: list[dict] = []
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


QUESTIONS: list[dict] = _load_questions()

# ---------------------------------------------------------------------------
# Data: exam facts (official, high-level facts only -- no invented stats)
# ---------------------------------------------------------------------------

EXAMS: dict[str, dict] = {
    "CompTIA Security+ (SY0-701)": {
        "vendor": "CompTIA",
        "code": "SY0-701",
        "about": "Core cybersecurity certification covering threats, architecture, "
        "operations, and governance. Aimed at IT professionals moving into "
        "security roles.",
    },
    "CompTIA Network+ (N10-009)": {
        "vendor": "CompTIA",
        "code": "N10-009",
        "about": "Vendor-neutral networking certification covering concepts, "
        "operations, and network security. Aimed at network technicians and "
        "administrators.",
    },
    "CompTIA A+ (220-1201 & 220-1202)": {
        "vendor": "CompTIA",
        "code": "220-1201 / 220-1202",
        "about": "Entry-level IT certification covering hardware, operating systems, "
        "networking, and operational procedures. Aimed at help-desk and support roles.",
    },
    "CompTIA Cloud+ (CV0-004)": {
        "vendor": "CompTIA",
        "code": "CV0-004",
        "about": "Cloud infrastructure certification covering architecture, "
        "deployment, and security. Aimed at cloud engineers and administrators.",
    },
    "CompTIA CySA+ (CS0-003)": {
        "vendor": "CompTIA",
        "code": "CS0-003",
        "about": "Cybersecurity analyst certification focused on threat detection, "
        "vulnerability management, and incident response.",
    },
    "CompTIA Linux+ (XK0-006)": {
        "vendor": "CompTIA",
        "code": "XK0-006",
        "about": "Linux system administration certification. Aimed at Linux "
        "administrators and DevOps-adjacent roles.",
    },
    "CompTIA PenTest+ (PT0-003)": {
        "vendor": "CompTIA",
        "code": "PT0-003",
        "about": "Penetration testing certification covering planning, exploitation, "
        "and reporting. Aimed at aspiring pentesters and red-teamers.",
    },
    "Cisco CCNA (200-301)": {
        "vendor": "Cisco",
        "code": "200-301",
        "about": "Foundational Cisco networking certification covering routing, "
        "switching, IP services, and security fundamentals.",
    },
    "AWS Certified Cloud Practitioner (CLF-C02)": {
        "vendor": "Amazon Web Services",
        "code": "CLF-C02",
        "about": "Entry-level AWS certification covering cloud concepts, security, "
        "and billing. Aimed at beginners and non-technical roles working with AWS.",
    },
    "AWS Certified AI Practitioner (AIF-C01)": {
        "vendor": "Amazon Web Services",
        "code": "AIF-C01",
        "about": "Entry-level AWS certification covering AI/ML and generative AI "
        "fundamentals and responsible AI.",
    },
    "Microsoft Azure Fundamentals (AZ-900)": {
        "vendor": "Microsoft",
        "code": "AZ-900",
        "about": "Entry-level Azure certification covering cloud concepts and Azure "
        "services, pricing, and governance.",
    },
    "Microsoft AI-901": {
        "vendor": "Microsoft",
        "code": "AI-901",
        "about": "Microsoft's entry-level AI certification, covering AI concepts and "
        "Microsoft AI services. Successor to the retired AI-900.",
    },
    "ISC2 CISSP": {
        "vendor": "ISC2",
        "code": "CISSP",
        "about": "Advanced security leadership certification across eight domains, "
        "from risk management to software development security. Requires "
        "professional experience; see isc2.org for current requirements.",
    },
    "ISC2 Certified in Cybersecurity (CC)": {
        "vendor": "ISC2",
        "code": "CC",
        "about": "Entry-level ISC2 certification covering security principles, "
        "business continuity, and security operations.",
    },
    "Certified Kubernetes Administrator (CKA)": {
        "vendor": "Cloud Native Computing Foundation",
        "code": "CKA",
        "about": "Hands-on Kubernetes administration certification. Performance-based "
        "exam aimed at cluster administrators.",
    },
    "Certified Kubernetes Application Developer (CKAD)": {
        "vendor": "Cloud Native Computing Foundation",
        "code": "CKAD",
        "about": "Hands-on Kubernetes certification for developers building and "
        "deploying cloud-native applications.",
    },
    "Docker Certified Associate (DCA)": {
        "vendor": "Docker",
        "code": "DCA",
        "about": "Docker platform certification covering images, containers, "
        "networking, storage, and orchestration basics.",
    },
    "NCLEX-RN": {
        "vendor": "NCSBN",
        "code": "NCLEX-RN",
        "about": "Licensure examination for registered nurses in the US and Canada. "
        "Required to practice as an RN.",
    },
    "Family Nurse Practitioner (FNP)": {
        "vendor": "AANP / ANCC",
        "code": "FNP",
        "about": "Certification for family nurse practitioners, covering primary care "
        "across the lifespan.",
    },
    "PMHNP-BC": {
        "vendor": "ANCC",
        "code": "PMHNP-BC",
        "about": "Board certification for psychiatric-mental health nurse practitioners.",
    },
    "Adult CCRN": {
        "vendor": "AACN",
        "code": "CCRN (Adult)",
        "about": "Critical care nursing certification for RNs caring for acutely and "
        "critically ill adult patients.",
    },
    "TEAS 7": {
        "vendor": "ATI",
        "code": "TEAS 7",
        "about": "Test of Essential Academic Skills, the nursing school entrance exam "
        "covering reading, math, science, and English.",
    },
}

# Aliases so users can type "security+", "sy0-701", "ccna", etc.
EXAM_ALIASES: dict[str, str] = {
    "security+": "CompTIA Security+ (SY0-701)",
    "security plus": "CompTIA Security+ (SY0-701)",
    "sy0-701": "CompTIA Security+ (SY0-701)",
    "sy0701": "CompTIA Security+ (SY0-701)",
    "sec+": "CompTIA Security+ (SY0-701)",
    "network+": "CompTIA Network+ (N10-009)",
    "network plus": "CompTIA Network+ (N10-009)",
    "n10-009": "CompTIA Network+ (N10-009)",
    "net+": "CompTIA Network+ (N10-009)",
    "a+": "CompTIA A+ (220-1201 & 220-1202)",
    "a plus": "CompTIA A+ (220-1201 & 220-1202)",
    "220-1101": "CompTIA A+ (220-1201 & 220-1202)",
    "220-1102": "CompTIA A+ (220-1201 & 220-1202)",
    "220-1201": "CompTIA A+ (220-1201 & 220-1202)",
    "220-1202": "CompTIA A+ (220-1201 & 220-1202)",
    "cloud+": "CompTIA Cloud+ (CV0-004)",
    "cloud plus": "CompTIA Cloud+ (CV0-004)",
    "cv0-004": "CompTIA Cloud+ (CV0-004)",
    "cysa+": "CompTIA CySA+ (CS0-003)",
    "cysa": "CompTIA CySA+ (CS0-003)",
    "cs0-003": "CompTIA CySA+ (CS0-003)",
    "linux+": "CompTIA Linux+ (XK0-006)",
    "linux plus": "CompTIA Linux+ (XK0-006)",
    "xk0-006": "CompTIA Linux+ (XK0-006)",
    "pentest+": "CompTIA PenTest+ (PT0-003)",
    "pentest plus": "CompTIA PenTest+ (PT0-003)",
    "pt0-003": "CompTIA PenTest+ (PT0-003)",
    "pen test+": "CompTIA PenTest+ (PT0-003)",
    "ccna": "Cisco CCNA (200-301)",
    "200-301": "Cisco CCNA (200-301)",
    "cisco": "Cisco CCNA (200-301)",
    "clf-c02": "AWS Certified Cloud Practitioner (CLF-C02)",
    "cloud practitioner": "AWS Certified Cloud Practitioner (CLF-C02)",
    "aif-c01": "AWS Certified AI Practitioner (AIF-C01)",
    "ai practitioner": "AWS Certified AI Practitioner (AIF-C01)",
    "az-900": "Microsoft Azure Fundamentals (AZ-900)",
    "azure fundamentals": "Microsoft Azure Fundamentals (AZ-900)",
    "ai-901": "Microsoft AI-901",
    "ai-900": "Microsoft AI-901",
    "cissp": "ISC2 CISSP",
    "isc2 cc": "ISC2 Certified in Cybersecurity (CC)",
    "certified in cybersecurity": "ISC2 Certified in Cybersecurity (CC)",
    "cka": "Certified Kubernetes Administrator (CKA)",
    "kubernetes administrator": "Certified Kubernetes Administrator (CKA)",
    "ckad": "Certified Kubernetes Application Developer (CKAD)",
    "kubernetes developer": "Certified Kubernetes Application Developer (CKAD)",
    "dca": "Docker Certified Associate (DCA)",
    "docker": "Docker Certified Associate (DCA)",
    "nclex": "NCLEX-RN",
    "nclex-rn": "NCLEX-RN",
    "fnp": "Family Nurse Practitioner (FNP)",
    "family nurse practitioner": "Family Nurse Practitioner (FNP)",
    "pmhnp": "PMHNP-BC",
    "pmhnp-bc": "PMHNP-BC",
    "psych np": "PMHNP-BC",
    "ccrn": "Adult CCRN",
    "adult ccrn": "Adult CCRN",
    "critical care": "Adult CCRN",
    "teas": "TEAS 7",
    "teas 7": "TEAS 7",
    "nursing entrance": "TEAS 7",
}


def _resolve_exam(text: str | None) -> str | None:
    """Resolve free text to a canonical exam name, or None."""
    if not text:
        return None
    key = text.strip().lower()
    if key in EXAM_ALIASES:
        return EXAM_ALIASES[key]
    # Substring matching so "Security+ practice pack" still resolves the exam.
    # Longer aliases first so "security+" wins over shorter overlaps.
    for alias in sorted(EXAM_ALIASES, key=len, reverse=True):
        if alias in key:
            return EXAM_ALIASES[alias]
    for exam in EXAMS:
        if key in exam.lower() or exam.lower() in key:
            return exam
    return None


# ---------------------------------------------------------------------------
# Data: product catalog
# ---------------------------------------------------------------------------

PRODUCT_TYPES = [
    {
        "type": "Study Guide",
        "price": 5,
        "questions": "100+ practice questions with explanations, plus full teaching chapters",
        "blurb": "Teaches the exam domain by domain, then tests you.",
    },
    {
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "blurb": "Pure practice: 100+ questions, every answer explained.",
    },
    {
        "type": "Complete Bundle",
        "price": 7,
        "questions": "200+ practice questions with explanations (guide + pack)",
        "blurb": "The study guide plus the practice pack together.",
    },
]

# Products with verified deep links (live on bytebarhq.com as of Sep 2026).
# Everything else resolves to the storefront / Etsy search.
VERIFIED_PRODUCTS = [
    {
        "name": "PenTest+ (PT0-003) Study Guide",
        "exam": "CompTIA PenTest+ (PT0-003)",
        "type": "Study Guide",
        "price": 5,
        "questions": "100+ practice questions with explanations, plus full teaching chapters",
        "url": "https://bytebarhq.com/b/J96h0",
    },
    {
        "name": "PenTest+ (PT0-003) Practice Pack",
        "exam": "CompTIA PenTest+ (PT0-003)",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/eZ7mN",
    },
    {
        "name": "PenTest+ (PT0-003) Complete Bundle",
        "exam": "CompTIA PenTest+ (PT0-003)",
        "type": "Complete Bundle",
        "price": 7,
        "questions": "200+ practice questions with explanations (guide + pack)",
        "url": "https://bytebarhq.com/b/hdvQC",
    },
    {
        "name": "NCLEX-RN Practice Pack",
        "exam": "NCLEX-RN",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/LuB10",
    },
    {
        "name": "FNP Practice Pack",
        "exam": "Family Nurse Practitioner (FNP)",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/7hkAj",
    },
    {
        "name": "PMHNP-BC Practice Pack",
        "exam": "PMHNP-BC",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/oQ4e0",
    },
    {
        "name": "Adult CCRN Practice Pack",
        "exam": "Adult CCRN",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/LZvcK",
    },
    {
        "name": "TEAS 7 Practice Pack",
        "exam": "TEAS 7",
        "type": "Practice Pack",
        "price": 3,
        "questions": "100+ practice questions with detailed answer explanations",
        "url": "https://bytebarhq.com/b/UvElu",
    },
]

STOREFRONT_URL = "https://bytebarhq.com"


def _etsy_search_url(exam: str) -> str:
    from urllib.parse import quote_plus

    return f"https://www.etsy.com/search?q={quote_plus('ByteBar ' + exam)}"


def _catalog_entry(exam: str, ptype: dict) -> dict:
    short = re.sub(r"\s*\(.*?\)\s*", "", exam).strip()
    return {
        "name": f"{exam} {ptype['type']}",
        "exam": exam,
        "type": ptype["type"],
        "price": ptype["price"],
        "questions": ptype["questions"],
        "blurb": ptype["blurb"],
        "url": STOREFRONT_URL,
        "etsy": _etsy_search_url(short or exam),
        "verified": False,
        "note": "Representative catalog entry — check bytebarhq.com for current availability.",
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_products(query: str, exam: str | None = None) -> dict:
    """Search the ByteBar exam-prep catalog.

    Args:
        query: What the user is looking for, e.g. "practice questions",
            "study guide", "bundle", "Security+", "NCLEX".
        exam: Optional exam name or code to narrow results
            (e.g. "Security+", "SY0-701", "NCLEX-RN", "CCNA").
    """
    q = (query or "").lower()
    target_exam = _resolve_exam(exam) or _resolve_exam(query)

    type_filter = None
    if any(w in q for w in ("study guide", "guide")):
        type_filter = "Study Guide"
    elif any(w in q for w in ("practice pack", "practice questions", "practice test", "questions")):
        type_filter = "Practice Pack"
    elif "bundle" in q:
        type_filter = "Complete Bundle"

    results: list[dict] = []

    # 1) Verified deep-link products first.
    for p in VERIFIED_PRODUCTS:
        if target_exam and p["exam"] != target_exam:
            continue
        if type_filter and p["type"] != type_filter:
            continue
        if not target_exam and type_filter is None:
            hay = (p["name"] + " " + p["exam"]).lower()
            if not any(tok in hay for tok in q.split()):
                continue
        results.append(
            {
                "name": p["name"],
                "exam": p["exam"],
                "type": p["type"],
                "price": p["price"],
                "questions": p["questions"],
                "url": p["url"],
                "verified": True,
            }
        )

    # 2) Representative catalog entries for the matched exam(s).
    exams = [target_exam] if target_exam else list(EXAMS)
    for ex in exams:
        for ptype in PRODUCT_TYPES:
            if type_filter and ptype["type"] != type_filter:
                continue
            if any(r.get("exam") == ex and r.get("type") == ptype["type"] for r in results):
                continue  # verified entry already covers it
            if target_exam is None and not any(
                tok in ex.lower() for tok in q.split() if len(tok) > 2
            ):
                continue
            results.append(_catalog_entry(ex, ptype))

    if not results:
        return {
            "results": [],
            "message": (
                "No catalog match. Available exams: " + ", ".join(sorted(EXAMS))
            ),
            "attribution": ATTRIBUTION,
        }

    return {
        "results": results[:20],
        "count": len(results),
        "attribution": ATTRIBUTION,
    }


@mcp.tool()
def get_free_questions(exam: str, domain: str | None = None, count: int = 5) -> dict:
    """Get free ByteBar practice questions for an exam.

    Serves only ByteBar's free-preview questions (the same free questions as
    the public Study Hub). Great for a quick quiz or sampling question style.

    Args:
        exam: Exam name or code, e.g. "Security+", "SY0-701", "NCLEX", "CCNA".
        domain: Optional domain/topic filter, e.g. "networking", "pharmacology".
        count: How many questions to return (1-10, default 5).
    """
    resolved = _resolve_exam(exam)
    if not resolved:
        return {
            "questions": [],
            "message": (
                f"Unknown exam '{exam}'. Free questions are available for: "
                + ", ".join(sorted({q["exam"] for q in QUESTIONS}))
            ),
            "attribution": ATTRIBUTION,
        }

    count = max(1, min(10, int(count or 5)))
    pool = [q for q in QUESTIONS if q["exam"] == resolved]
    if domain:
        d = domain.lower()
        pool = [q for q in pool if d in q.get("domain", "").lower()]

    out = []
    for q in pool[:count]:
        out.append(
            {
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": q["explanation"],
                "domain": q.get("domain", ""),
                "source_url": q.get("source_url", ""),
            }
        )

    return {
        "exam": resolved,
        "domain_filter": domain,
        "questions": out,
        "returned": len(out),
        "available": len(pool),
        "note": (
            "Free-preview questions from the ByteBar Study Hub. "
            "Full 100+ question packs at bytebarhq.com."
        ),
        "attribution": ATTRIBUTION,
    }


@mcp.tool()
def get_pricing() -> dict:
    """Get the ByteBar pricing table."""
    return {
        "products": [
            {
                "name": "Study Guide",
                "price_usd": 5,
                "includes": "Full teaching chapters + 100+ practice questions with explanations",
            },
            {
                "name": "Practice Pack",
                "price_usd": 3,
                "includes": "100+ practice questions with detailed answer explanations",
            },
            {
                "name": "Complete Bundle",
                "price_usd": 7,
                "includes": "Study Guide + Practice Pack (200+ questions total)",
            },
            {
                "name": "Trifecta Bundle",
                "price_usd": 14,
                "includes": "Multi-exam bundle (e.g. DevOps Quad: 800 questions across 4 exams)",
            },
        ],
        "store": STOREFRONT_URL,
        "attribution": ATTRIBUTION,
    }


@mcp.tool()
def get_exam_info(exam: str) -> dict:
    """Get high-level facts about a certification exam ByteBar covers.

    Returns the vendor, exam code, and who the cert is for. For current exam
    objectives, passing scores, and fees, always check the vendor's official site.

    Args:
        exam: Exam name or code, e.g. "Security+", "CISSP", "NCLEX-RN", "CKA".
    """
    resolved = _resolve_exam(exam)
    if not resolved:
        return {
            "exam": exam,
            "found": False,
            "message": "ByteBar covers: " + ", ".join(sorted(EXAMS)),
            "attribution": ATTRIBUTION,
        }
    info = EXAMS[resolved]
    return {
        "exam": resolved,
        "found": True,
        "vendor": info["vendor"],
        "code": info["code"],
        "about": info["about"],
        "free_questions": any(q["exam"] == resolved for q in QUESTIONS),
        "study_materials": f"Search bytebarhq.com for {resolved} prep materials.",
        "attribution": ATTRIBUTION,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _build_http_app() -> "Starlette":
    """MCP Starlette app plus /healthz and a landing page.

    Extra routes are appended directly to the MCP app's own routes so the
    /mcp endpoint keeps its exact routing behavior.
    """
    from starlette.responses import JSONResponse, PlainTextResponse
    from starlette.routing import Route

    mcp_app = mcp.streamable_http_app()

    async def healthz(_request):
        return JSONResponse(
            {"status": "ok", "server": "bytebar", "tools": 4, "transport": "streamable-http"}
        )

    async def index(_request):
        return PlainTextResponse(
            "ByteBar MCP Server\n"
            "MCP endpoint: POST /mcp (Streamable HTTP)\n"
            "Health: GET /healthz\n"
            "More exam prep: https://bytebarhq.com\n"
        )

    mcp_app.routes.append(Route("/healthz", healthz))
    mcp_app.routes.append(Route("/", index))
    return mcp_app


def main() -> None:
    parser = argparse.ArgumentParser(description="ByteBar MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport to use (default: stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transports")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transports")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        import uvicorn

        uvicorn.run(_build_http_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
