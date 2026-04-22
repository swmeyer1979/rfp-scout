#!/usr/bin/env python3
"""
RFP Scout - SAM.gov Opportunity Scanner
Scans SAM.gov for active RFPs matching consulting boutique capabilities.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SAM_API_KEY = os.getenv("SAM_API_KEY", "")
SAM_BASE_URL = "https://api.sam.gov/opportunities/v2/search"
RESULTS_FILE = os.getenv("RESULTS_FILE", "rfps.json")

KEYWORDS = [
    "management consulting", "IT services", "cybersecurity", "artificial intelligence",
    "machine learning", "data analytics", "systems engineering", "technical assistance",
    "program management", "strategic planning", "digital transformation", "cloud migration",
    "software development", "human centered design", "agile coaching",
]

TARGET_NAICS = [
    "541511", "541512", "541513", "541519", "541611", "541612", "541613",
    "541618", "541690", "541990",
]
HIGH_VALUE_NAICS = ["541611", "541612", "541613", "541618", "541690", "541990"]

SET_ASIDE_SCORES = {"NONE": 2, "SB": 3, "SBA": 3, "8A": 2, "HZ": 2, "SDVOSB": 2, "WOSB": 2, "EDWOSB": 2, "VOSB": 2, "HUBZone": 2}


class RFPOpportunity:
    def __init__(self, raw: dict):
        self.notice_id = raw.get("noticeId", "")
        self.title = raw.get("title", "Untitled")
        self.solicitation_number = raw.get("solicitationNumber", "")
        self.agency = raw.get("fullParentPathName", "Unknown Agency")
        self.naics_code = str(raw.get("naicsCode", "")).strip()
        self.set_aside = self._extract_set_aside(raw)
        self.due_date = raw.get("responseDeadLine", "")
        self.publish_date = raw.get("publishDate", "")
        self.description = raw.get("description", "")[:800]
        self.url = f"https://sam.gov/opp/{self.notice_id}/view"
        self.type_of_set_aside_description = raw.get("typeOfSetAsideDescription", "")
        self.primary_contact = raw.get("primaryContact", {})
        award = raw.get("award", {}) or {}
        self.estimated_value = award.get("estimatedTotalContractValue", "") or award.get("awardAmount", "")
        self.estimated_value = self.estimated_value or "Not Specified"

    def _extract_set_aside(self, raw: dict) -> str:
        award = raw.get("award", {}) or {}
        code = award.get("typeOfSetAside") or raw.get("typeOfSetAside") or "NONE"
        return str(code).strip().upper()

    def to_dict(self) -> dict:
        return {
            "notice_id": self.notice_id, "title": self.title,
            "solicitation_number": self.solicitation_number, "agency": self.agency,
            "naics_code": self.naics_code, "set_aside": self.set_aside,
            "set_aside_description": self.type_of_set_aside_description,
            "due_date": self.due_date, "publish_date": self.publish_date,
            "estimated_value": str(self.estimated_value), "description": self.description,
            "url": self.url,
            "primary_contact_email": self.primary_contact.get("email", ""),
            "primary_contact_phone": self.primary_contact.get("phone", ""),
        }


def fetch_opportunities(api_key: str, days_back: int = 30, limit: int = 100, keyword: Optional[str] = None) -> List[RFPOpportunity]:
    if not api_key:
        logger.error("SAM_API_KEY not set. Get one at https://sam.gov")
        return []
    posted_to = datetime.now().strftime("%m/%d/%Y")
    posted_from = (datetime.now() - timedelta(days=days_back)).strftime("%m/%d/%Y")
    params = {"api_key": api_key, "postedFrom": posted_from, "postedTo": posted_to, "limit": min(limit, 1000), "offset": 0}
    if keyword:
        params["title"] = keyword
    url = f"{SAM_BASE_URL}?{urlencode(params)}"
    logger.info("Fetching: %s", url.replace(api_key, "***"))
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error("SAM.gov API error: %s", e)
        return []
    records = data.get("opportunitiesData", []) or []
    opportunities = []
    for rec in records:
        try:
            opp = RFPOpportunity(rec)
            opportunities.append(opp)
        except Exception as e:
            logger.warning("Skipping malformed record: %s", e)
    return opportunities


def score_opportunity(opp: RFPOpportunity) -> int:
    score = 0
    score += SET_ASIDE_SCORES.get(opp.set_aside, 1)
    if opp.naics_code in HIGH_VALUE_NAICS:
        score += 2
    elif opp.naics_code in TARGET_NAICS:
        score += 1
    try:
        due = datetime.strptime(opp.due_date[:10], "%Y-%m-%d")
        days_to_due = (due - datetime.now()).days
        if days_to_due >= 14: score += 2
        elif days_to_due >= 7: score += 1
    except Exception:
        score += 1
    val_str = str(opp.estimated_value).replace(",", "").replace("$", "").strip()
    try:
        val = float(val_str) if val_str and val_str.lower() not in ("not specified", "n/a", "") else 0
        if 150_000 <= val <= 5_000_000: score += 2
        elif 50_000 <= val < 150_000: score += 1
        else: score += 1
    except Exception:
        score += 1
    text = f"{opp.title} {opp.description}".lower()
    kw_hits = sum(1 for k in KEYWORDS if k.lower() in text)
    if kw_hits >= 2: score += 1
    return min(score, 10)


def filter_and_score(opportunities: List[RFPOpportunity]) -> List[Dict]:
    results = []
    for opp in opportunities:
        if opp.set_aside in ("AWARDED", "CLOSED"):
            continue
        score = score_opportunity(opp)
        if score >= 4:
            d = opp.to_dict()
            d["boutique_fit_score"] = score
            results.append(d)
    results.sort(key=lambda x: x["boutique_fit_score"], reverse=True)
    return results


def main():
    logger.info("RFP Scout scanner starting...")
    all_opps: List[RFPOpportunity] = []
    search_terms = ["management consulting", "IT services", "cybersecurity", "data analytics", "technical assistance"]
    for term in search_terms:
        opps = fetch_opportunities(SAM_API_KEY, days_back=14, limit=100, keyword=term)
        all_opps.extend(opps)
        logger.info("Keyword '%s' returned %d results", term, len(opps))
    seen = set()
    unique = []
    for o in all_opps:
        if o.notice_id not in seen:
            seen.add(o.notice_id)
            unique.append(o)
    scored = filter_and_score(unique)
    logger.info("Found %d scored opportunities", len(scored))
    with open(RESULTS_FILE, "w") as f:
        json.dump(scored, f, indent=2)
    logger.info("Results written to %s", RESULTS_FILE)


if __name__ == "__main__":
    main()
