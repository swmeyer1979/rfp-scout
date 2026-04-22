#!/usr/bin/env python3
"""
RFP Scout - Alert Generator
Generates daily email digest + optional AI compliance matrix (premium).
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RESULTS_FILE = os.getenv("RESULTS_FILE", "rfps.json")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "moonshotai/kimi-k2.6")
TOP_N = int(os.getenv("TOP_N", "10"))
TIER = os.getenv("TIER", "basic")


def load_top_rfps(path: str, n: int = 10) -> List[Dict]:
    if not os.path.exists(path):
        logger.error("Results file not found: %s", path)
        return []
    with open(path) as f:
        data = json.load(f)
    return data[:n]


def generate_summary(rfps: List[Dict]) -> str:
    lines = [
        "# RFP Scout Daily Digest",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"**Tier:** {TIER.capitalize()}",
        f"**Opportunities:** {len(rfps)}",
        "---",
    ]
    for i, r in enumerate(rfps, 1):
        lines.append(f"### {i}. {r['title']}")
        lines.append(f"- **Agency:** {r['agency']}")
        lines.append(f"- **NAICS:** {r['naics_code']}")
        lines.append(f"- **Set-Aside:** {r['set_aside_description'] or r['set_aside']}")
        lines.append(f"- **Due Date:** {r['due_date']}")
        lines.append(f"- **Est. Value:** {r['estimated_value']}")
        lines.append(f"- **Boutique Fit Score:** {r['boutique_fit_score']}/10")
        lines.append(f"- **Link:** {r['url']}")
        lines.append(f"- **Description:** {r['description'][:300]}...")
        lines.append("")
    return "\n".join(lines)


def generate_compliance_matrix(rfp: Dict) -> str:
    if not OPENROUTER_API_KEY:
        return "> Compliance matrix requires OPENROUTER_API_KEY (Premium tier)"
    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
    system_prompt = (
        "You are an expert government proposal writer. Given an RFP summary, "
        "generate a compliance matrix table with three columns: "
        "Requirement, Where Addressed, and Boutique Response. "
        "Focus on how a 5-50 person consulting boutique can realistically meet each requirement."
    )
    user_prompt = f"""RFP Title: {rfp['title']}
Agency: {rfp['agency']}
NAICS: {rfp['naics_code']}
Due Date: {rfp['due_date']}
Description: {rfp['description']}

Generate a concise compliance matrix and a 4-section proposal outline.
"""
    try:
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.4, max_tokens=1500,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error("AI generation failed for %s: %s", rfp.get("notice_id"), e)
        return f"> AI generation failed: {e}"


def build_html_email(markdown_digest: str, premium_matrices: List[str]) -> str:
    import html
    body = f"""<html><head><style>
body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; }}
h1 {{ color: #1a3c6c; }} h2, h3 {{ color: #2c5282; }}
pre {{ background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #1a3c6c; color: white; }}
</style></head><body>
<h1>RFP Scout Daily Digest</h1>
<p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}<br><strong>Tier:</strong> {TIER.capitalize()}</p><hr>
<pre>{html.escape(markdown_digest)}</pre>
"""
    if TIER == "premium" and premium_matrices:
        body += "<h2>Premium: AI Compliance Matrices</h2>"
        for idx, matrix in enumerate(premium_matrices, 1):
            body += f"<h3>Opportunity #{idx}</h3><pre>{html.escape(matrix)}</pre><hr>"
    body += "<p style='color:#666;font-size:12px;'>RFP Scout | Never miss a winnable government RFP again.</p></body></html>"
    return body


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rfps = load_top_rfps(RESULTS_FILE, TOP_N)
    if not rfps:
        logger.warning("No RFPs to process.")
        return
    digest_md = generate_summary(rfps)
    md_path = os.path.join(OUTPUT_DIR, f"digest_{datetime.now().strftime('%Y%m%d')}.md")
    with open(md_path, "w") as f:
        f.write(digest_md)
    logger.info("Digest written to %s", md_path)
    matrices = []
    if TIER == "premium":
        logger.info("Generating premium compliance matrices...")
        for rfp in rfps:
            matrices.append(generate_compliance_matrix(rfp))
    html_email = build_html_email(digest_md, matrices)
    html_path = os.path.join(OUTPUT_DIR, f"email_{datetime.now().strftime('%Y%m%d')}.html")
    with open(html_path, "w") as f:
        f.write(html_email)
    logger.info("HTML email written to %s", html_path)
    print(digest_md)


if __name__ == "__main__":
    main()
