"""
PubMed E-utilities wrapper — fetch recent articles about a medical condition.
Public API, no auth required (rate-limited to ~3/s without key).
"""
from __future__ import annotations

import time
import xml.etree.ElementTree as ET
from typing import Optional

import requests

from .models import PubMedArticle

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fg"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_USER_AGENT = "triallight/1.0 (https://github.com/akshattandon007/LLM-Apps)"


def search_articles(condition: str, max_results: int = 5) -> list[PubMedArticle]:
    """Search PubMed for recent articles about a condition.

    Returns up to `max_results` PubMedArticle objects.
    """
    # Step 1: ESearch to get PMIDs
    search_params = {
        "db": "pubmed",
        "term": condition,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }
    resp = requests.get(
        ESEARCH_URL,
        params=search_params,
        headers={"User-Agent": _USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        return []

    # Step 2: EFetch to get article details (abstracts)
    ids_comma = ",".join(id_list)
    fetch_params = {
        "db": "pubmed",
        "id": ids_comma,
        "retmode": "xml",
        "rettype": "abstract",
    }
    time.sleep(0.4)  # rate limit courtesy
    resp2 = requests.get(
        EFETCH_URL,
        params=fetch_params,
        headers={"User-Agent": _USER_AGENT},
        timeout=30,
    )
    resp2.raise_for_status()

    articles = _parse_pubmed_xml(resp2.text, id_list)
    return articles


def _parse_pubmed_xml(xml_text: str, pmid_order: list[str]) -> list[PubMedArticle]:
    """Parse PubMed XML efetch response into PubMedArticle objects."""
    articles: list[PubMedArticle] = []
    root = ET.fromstring(xml_text)

    pmid_set = set(pmid_order)
    for pubmed_article in root.findall(".//PubmedArticle"):
        medline = pubmed_article.find(".//MedlineCitation")
        if medline is None:
            continue

        pmid_elem = medline.find("./PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        if pmid not in pmid_set:
            continue

        article = medline.find("./Article")
        if article is None:
            continue

        title_elem = article.find("./Title")
        title = title_elem.text if title_elem is not None else ""

        # Authors
        author_list = article.find("./AuthorList")
        authors = ""
        if author_list is not None:
            auth_names = []
            for author in author_list.findall("./Author"):
                ln = author.find("./LastName")
                if ln is not None:
                    auth_names.append(ln.text)
            authors = ", ".join(auth_names[:5])

        # Journal
        journal_elem = article.find("./Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # Year
        year_elem = article.find("./Journal/JournalIssue/PubDate/Year")
        year = year_elem.text if year_elem is not None else ""

        # Abstract
        abstract_text = ""
        abstract_elem = article.find("./Abstract")
        if abstract_elem is not None:
            parts = []
            for at in abstract_elem.findall("./AbstractText"):
                label = at.get("Label", "")
                text = (at.text or "")
                if label:
                    parts.append(f"{label}: {text}")
                else:
                    parts.append(text)
            abstract_text = " ".join(parts)

        articles.append(
            PubMedArticle(
                pmid=pmid,
                title=title or "",
                authors=authors,
                journal=journal or "",
                year=year or "",
                abstract=abstract_text,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            )
        )

    return articles