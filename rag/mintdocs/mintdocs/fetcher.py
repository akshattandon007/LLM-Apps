"""Fetch SEC filings from EDGAR API."""

import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Optional

import httpx

from .models import FilingMetadata

# SEC requires a User-Agent with contact email + descriptive name
USER_AGENT = "MintDocs Research/1.0 (contact@mintdocs.dev)"
SEC_BASE = "https://www.sec.gov"
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
CIK_LOOKUP_URL = f"{SEC_BASE}/files/company_tickers.json"
CIK_EXCHANGE_URL = f"{SEC_BASE}/files/company_tickers_exchange.json"

# Rate limiting: SEC says 10 req/s, we'll be conservative
REQUEST_DELAY = 0.15  # seconds between requests


class FetcherError(Exception):
    """Raised when a fetch operation fails."""


class Fetcher:
    """Fetch and resolve SEC filings for a given ticker."""

    def __init__(self, user_agent: str = USER_AGENT, simulate: bool = False):
        self.user_agent = user_agent
        self.simulate = simulate
        self._cik_cache: dict[str, dict] = {}
        self._client = httpx.Client(
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------
    # CIK Resolution
    # ------------------------------------------------------------------

    def _load_cik_map(self) -> dict[str, dict]:
        """Load the CIK ticker map from SEC's bulk file (cached in-memory)."""
        if self._cik_cache:
            return self._cik_cache

        resp = self._client.get(CIK_LOOKUP_URL)
        resp.raise_for_status()
        data = resp.json()

        # SEC returns a dict keyed by integer index with inner fields
        lookup: dict[str, dict] = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").strip().upper()
            if ticker:
                cik_str = str(entry["cik_str"]).zfill(10)
                lookup[ticker] = {
                    "cik": cik_str,
                    "name": entry.get("title", ""),
                }
        self._cik_cache = lookup
        return lookup

    def resolve_cik(self, ticker: str) -> str:
        """Resolve a stock ticker to a 10-digit CIK number."""
        if self.simulate:
            return "0000320193"  # Apple's CIK for simulated mode

        lookup = self._load_cik_map()
        ticker = ticker.strip().upper()
        if ticker not in lookup:
            raise FetcherError(f"Ticker '{ticker}' not found in SEC CIK database")
        return lookup[ticker]["cik"]

    def resolve_company_name(self, ticker: str) -> str:
        """Resolve ticker to company name."""
        if self.simulate:
            return f"{ticker.upper()} Inc. (Simulated)"

        lookup = self._load_cik_map()
        ticker = ticker.strip().upper()
        if ticker not in lookup:
            raise FetcherError(f"Ticker '{ticker}' not found")
        return lookup[ticker]["name"]

    # ------------------------------------------------------------------
    # Filing Search via EDGAR Full-Text Search (EFTS)
    # ------------------------------------------------------------------

    def search_filings(
        self,
        ticker: str,
        forms: list[str] | None = None,
        quarters: int = 8,
    ) -> list[dict]:
        """Search for recent filings using the SEC EFTS API.

        Returns a list of filing result dicts with accession numbers.
        """
        if forms is None:
            forms = ["10-K", "10-Q"]

        if self.simulate:
            return self._simulate_search_results(ticker, forms, quarters)

        cik = self.resolve_cik(ticker)
        company_name = self.resolve_company_name(ticker)

        # Build query: CIK + form types
        # SEC EFTS uses q parameter with fielded search
        form_query = " OR ".join(f'formType:"{f}"' for f in forms)
        query = f'cik:"{cik}" AND ({form_query})'

        params = {
            "q": query,
            "dateRange": "all",
            "startdt": "",  # no date filter — we'll limit by count
            "enddt": "",
            "sort": "filedAt desc",
        }

        resp = self._client.get(EFTS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        raw_hits = data.get("hits", {}).get("hits", [])
        results = []
        for hit in raw_hits:
            source = hit.get("_source", {})
            accession = source.get("accessionNumber", "").replace("-", "")
            filing_type = source.get("formType", "")
            filed_at = source.get("filedAt", "")[:10]  # YYYY-MM-DD

            # Skip if we have enough of each type
            results.append(
                {
                    "cik": cik,
                    "company_name": company_name,
                    "ticker": ticker.upper(),
                    "filing_type": filing_type,
                    "filing_date": filed_at,
                    "accession_number": accession,
                    "primary_doc": self._get_primary_doc(source),
                }
            )

        return results[:quarters]

    def _get_primary_doc(self, source: dict) -> str:
        """Extract the primary document URL from a search hit."""
        # The primary doc is typically the full-submission text file
        # SEC uses the accession number to build the URL
        accession = source.get("accessionNumber", "")
        cik = source.get("cik", "")
        if not accession or not cik:
            return ""
        # Remove hyphens for URL construction
        accession_clean = accession.replace("-", "")
        # First doc is usually the full submission
        primary_doc = source.get("primaryDoc", "")
        if primary_doc:
            # If it's just a filename, build the full URL
            if not primary_doc.startswith("http"):
                primary_doc = (
                    f"{SEC_BASE}/Archives/edgar/data/{cik}/"
                    f"{accession_clean}/{primary_doc}"
                )
            return primary_doc
        # Fallback: construct the full submission text URL
        return (
            f"{SEC_BASE}/Archives/edgar/data/{cik}/"
            f"{accession_clean}/{accession_clean}.txt"
        )

    # ------------------------------------------------------------------
    # Filing Content Fetch
    # ------------------------------------------------------------------

    def fetch_filing_text(self, filing: dict) -> str:
        """Download the full text of an SEC filing."""
        if self.simulate:
            return self._simulate_filing_text(filing)

        url = filing.get("primary_doc")
        if not url:
            raise FetcherError("No primary document URL available")

        # Rate-limit SEC requests
        time.sleep(REQUEST_DELAY)

        resp = self._client.get(url)
        resp.raise_for_status()

        # SEC returns text/html for filings; extract readable text
        text = resp.text
        # Strip HTML tags for readability
        clean = re.sub(r"<[^>]+>", " ", text)
        # Collapse multiple whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def fetch_all(
        self,
        ticker: str,
        forms: list[str] | None = None,
        quarters: int = 8,
    ) -> list[FilingMetadata]:
        """Search for filings and return FilingMetadata objects."""
        results = self.search_filings(ticker, forms, quarters)
        metadata_list = []
        for r in results:
            try:
                filing_date = date.fromisoformat(r["filing_date"])
            except (ValueError, TypeError):
                filing_date = date.today()
            metadata_list.append(
                FilingMetadata(
                    company_name=r["company_name"],
                    ticker=r["ticker"],
                    cik=r["cik"],
                    filing_type=r["filing_type"],
                    filing_date=filing_date,
                    accession_number=r["accession_number"],
                    primary_doc=r["primary_doc"],
                )
            )
        return metadata_list

    # ------------------------------------------------------------------
    # Simulated mode helpers
    # ------------------------------------------------------------------

    def _simulate_search_results(
        self, ticker: str, forms: list[str], quarters: int
    ) -> list[dict]:
        """Generate fake but realistic-looking search results."""
        cik = self.resolve_cik(ticker)
        company_name = self.resolve_company_name(ticker)
        ticker_up = ticker.upper()

        # Alternate 10-K and 10-Q going back in time
        results = []
        for i in range(quarters):
            if i % 3 == 0:
                ftype = "10-K"
                # Every 4th quarter is a 10-K
                year = 2024 - (i // 3)
                month = "10"
                day = f"{28 - (i % 3):02d}"
            else:
                ftype = "10-Q"
                q_num = i % 3
                year = 2024 - (i // 3)
                month = f"{4 * q_num - 1:02d}" if q_num > 0 else "01"
                month = month if 1 <= int(month) <= 12 else "07"
                day = f"{15:02d}"

            acc = f"0000320193-{2024 - i}-{100000 + i:06d}"
            acc_clean = acc.replace("-", "")
            results.append(
                {
                    "cik": cik,
                    "company_name": company_name,
                    "ticker": ticker_up,
                    "filing_type": ftype,
                    "filing_date": f"{year}-{month}-{day}",
                    "accession_number": acc_clean,
                    "primary_doc": (
                        f"{SEC_BASE}/Archives/edgar/data/{cik}/"
                        f"{acc_clean}/{acc_clean}.txt"
                    ),
                }
            )
        return results

    def _simulate_filing_text(self, filing: dict) -> str:
        """Generate realistic simulated filing text for demo mode."""
        ftype = filing["filing_type"]
        company = filing["company_name"]
        year = filing["filing_date"][:4]

        if ftype == "10-K":
            return self._simulated_10k(company, year)
        return self._simulated_10q(company, year)

    def _simulated_10k(self, company: str, year: str) -> str:
        return f"""
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
FORM 10-K ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d)
For the fiscal year ended September 28, {year}

Commission File Number: 001-XXXXX

{company}

Item 1. Business
{company} designs, manufactures, and markets smartphones, personal computers,
tablets, wearables, and accessories worldwide. The Company also sells digital
content and services, including streaming, cloud storage, and productivity
software. The Company operates through geographic segments: Americas, Europe,
Greater China, Japan, and Rest of Asia Pacific.

Item 1A. Risk Factors
Investing in {company} involves various risks. The Company's operations are
subject to global economic conditions, supply chain disruptions, and
geopolitical tensions. The Company relies on a complex global supply chain
network concentrated in Asia, particularly China. Any disruption to this supply
chain, including trade disputes, natural disasters, or public health crises,
could materially impact the Company's ability to manufacture products. The
Company faces intense competition in all markets, and failure to innovate could
reduce market share. Changes in tax policies, tariffs, and import/export
regulations could increase costs. The Company's international operations are
subject to currency fluctuations and foreign legal requirements.

Item 1B. Unresolved Staff Comments
None.

Item 2. Properties
The Company's corporate headquarters are located in Cupertino, California. The
Company leases and owns facilities worldwide for manufacturing, research and
development, retail, and data center operations.

Item 3. Legal Proceedings
The Company is subject to various legal proceedings and claims that have arisen
in the ordinary course of business. Management does not believe that the
outcome of these matters will have a material adverse effect on the Company's
financial condition.

Item 4. Mine Safety Disclosures
Not applicable.

Item 5. Market for Registrant's Common Equity, Related Stockholder Matters
and Issuer Purchases of Equity Securities
The Company's common stock is listed on The Nasdaq Stock Market under the
symbol AAPL. As of October 31, {year}, there were approximately 15.3 billion
shares outstanding held by approximately 25,000 stockholders of record.

Item 6. [Reserved]

Item 7. Management's Discussion and Analysis of Financial Condition
and Results of Operations
Revenue for fiscal year {year} was $391.0 billion, a decrease of 3% from the
prior year. Products revenue declined 4% to $298.0 billion, while Services
revenue grew 6% to $93.0 billion. Gross margin was 44.1%, compared to 43.3%
in the prior year. The increase was driven by a richer mix of Services revenue
and improved product margins. Operating expenses were $54.0 billion, up 5%
year over year. Net income was $97.0 billion, compared to $99.8 billion in the
prior year. Cash generated from operations was $110.0 billion.

Item 7A. Quantitative and Qualitative Disclosures About Market Risk
The Company is exposed to interest rate risk on its investment portfolio and
foreign currency exchange risk on its global operations. A 10% strengthening
of the US dollar against foreign currencies would decrease revenue by
approximately $4.5 billion.

Item 8. Financial Statements and Supplementary Data
See the consolidated financial statements starting on page 32 of this Annual
Report on Form 10-K.

Item 9. Changes in and Disagreements With Accountants on Accounting
and Financial Disclosure
None.

Item 9A. Controls and Procedures
The Company maintains disclosure controls and procedures designed to ensure
that information required to be disclosed is recorded, processed, summarized,
and reported within the time periods specified. Management assessed the
effectiveness of internal control over financial reporting as of September 28,
{year} and concluded that it was effective.

Item 9B. Other Information
None.

Item 9C. Disclosure Regarding Foreign Jurisdictions that Prevent Inspections
Not applicable.

Item 10. Directors, Executive Officers and Corporate Governance
Information regarding directors and executive officers is incorporated by
reference from the Proxy Statement for the Annual Meeting of Shareholders.

Item 11. Executive Compensation
Incorporated by reference from the Proxy Statement.

Item 12. Security Ownership of Certain Beneficial Owners and Management
and Related Stockholder Matters
Incorporated by reference from the Proxy Statement.

Item 13. Certain Relationships and Related Transactions,
and Director Independence
Incorporated by reference from the Proxy Statement.

Item 14. Principal Accounting Fees and Services
Incorporated by reference from the Proxy Statement.

Item 15. Exhibits, Financial Statement Schedules
(a) Financial Statements: See Item 8.
(b) Exhibits: The exhibits listed in the Exhibit Index are filed herewith.

Item 16. Form 10-K Summary
None.
"""

    def _simulated_10q(self, company: str, year: str) -> str:
        return f"""
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
FORM 10-Q QUARTERLY REPORT PURSUANT TO SECTION 13 OR 15(d)
For the quarterly period ended {year}

{company}

Item 1. Financial Statements
The condensed consolidated financial statements for the quarter ended
{year} are included herein. Revenue was $94.8 billion, gross margin was
44.3%, and net income was $24.2 billion. Cash and marketable securities
totaled $162.0 billion.

Item 2. Management's Discussion and Analysis of Financial Condition
and Results of Operations
Revenue increased 5% year over year driven by strong Services growth and
iPhone sales in emerging markets. Services revenue reached a new all-time
record of $24.2 billion. The Company returned over $27 billion to
shareholders during the quarter through dividends and share repurchases.
Supply chain conditions have improved compared to the prior year period.

Item 3. Quantitative and Qualitative Disclosures About Market Risk
There have been no material changes in market risk exposures from those
disclosed in the Company's Annual Report on Form 10-K.

Item 4. Controls and Procedures
The Company's disclosure controls and procedures were effective as of the
end of the quarter. There were no changes in internal control over financial
reporting that materially affected, or are reasonably likely to materially
affect, such controls.

Part II — Other Information

Item 1. Legal Proceedings
There have been no material changes to legal proceedings previously
disclosed in the Annual Report.

Item 1A. Risk Factors
There have been no material changes to the risk factors previously disclosed
in the Annual Report on Form 10-K. The Company continues to monitor
geopolitical tensions, trade policies, and supply chain dynamics.

Item 2. Unregistered Sales of Equity Securities and Use of Proceeds
None.

Item 3. Defaults Upon Senior Securities
None.

Item 4. Mine Safety Disclosures
Not applicable.

Item 5. Other Information
None.

Item 6. Exhibits
The exhibits listed in the Exhibit Index are filed herewith.
"""