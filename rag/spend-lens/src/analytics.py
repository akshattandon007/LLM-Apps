"""
src/analytics.py
────────────────
Analytics layer for SpendLens.

Computes aggregate stats from normalised transactions:
  - Category breakdown (pie-chart ready)
  - Monthly totals / trends
  - Top merchants by spend
  - Subscription detection
  - Unusual spending alerts
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from document_loader import Transaction


def category_breakdown(
    transactions: List[Transaction],
    top_n: int = 10,
) -> Dict:
    """Return category-level spending breakdown.

    Returns a dict with:
        categories: list of {category, total, count, percent}
        total_spent: float
        total_income: float
    """
    cats: Dict[str, float] = defaultdict(float)
    cat_counts: Dict[str, int] = defaultdict(int)
    total_spent = 0.0
    total_income = 0.0

    for tx in transactions:
        if tx.amount < 0:
            cats[tx.category] += abs(tx.amount)
            cat_counts[tx.category] += 1
            total_spent += abs(tx.amount)
        else:
            total_income += tx.amount

    # Sort by spend descending, take top N
    sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
    if top_n:
        sorted_cats = sorted_cats[:top_n]

    categories = [
        {
            "category": cat,
            "total": round(amt, 2),
            "count": cat_counts[cat],
            "percent": round((amt / total_spent * 100) if total_spent > 0 else 0, 1),
        }
        for cat, amt in sorted_cats
    ]

    return {
        "categories": categories,
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "transaction_count": len(transactions),
    }


def monthly_totals(
    transactions: List[Transaction],
    months: int = 12,
) -> Dict:
    """Return month-by-month spending and income totals.

    Returns:
        months: list of {month, spent, income, net, count}
    """
    monthly: Dict[str, Dict] = defaultdict(lambda: {"spent": 0.0, "income": 0.0, "count": 0})

    for tx in transactions:
        month_key = tx.date[:7]  # YYYY-MM
        if tx.amount < 0:
            monthly[month_key]["spent"] += abs(tx.amount)
        else:
            monthly[month_key]["income"] += tx.amount
        monthly[month_key]["count"] += 1

    result = []
    for month_key in sorted(monthly.keys(), reverse=True)[:months]:
        m = monthly[month_key]
        result.append({
            "month": month_key,
            "spent": round(m["spent"], 2),
            "income": round(m["income"], 2),
            "net": round(m["income"] - m["spent"], 2),
            "count": m["count"],
        })

    # Sort chronologically for chart display
    result.reverse()

    return {"months": result}


def top_merchants(
    transactions: List[Transaction],
    top_n: int = 10,
    category: str | None = None,
) -> Dict:
    """Return top merchants by total spend.

    Parameters
    ----------
    transactions : All transactions.
    top_n        : Number of top merchants to return.
    category     : Optional filter by category.

    Returns:
        merchants: list of {merchant, total, count, average, category}
    """
    merchants: Dict[str, Dict] = defaultdict(lambda: {"total": 0.0, "count": 0, "category": ""})

    for tx in transactions:
        if tx.amount >= 0:
            continue  # only spending (debits)
        if category and tx.category != category:
            continue
        key = tx.description.lower()
        merchants[key]["total"] += abs(tx.amount)
        merchants[key]["count"] += 1
        merchants[key]["category"] = tx.category

    sorted_merchants = sorted(
        merchants.items(), key=lambda x: x[1]["total"], reverse=True
    )[:top_n]

    return {
        "merchants": [
            {
                "merchant": desc,
                "total": round(data["total"], 2),
                "count": data["count"],
                "average": round(data["total"] / data["count"], 2),
                "category": data["category"],
            }
            for desc, data in sorted_merchants
        ]
    }


def detect_subscriptions(
    transactions: List[Transaction],
    min_occurrences: int = 2,
) -> Dict:
    """Detect recurring payments that look like subscriptions.

    Looks for the same description appearing multiple times
    with similar amounts.
    """
    groups: Dict[str, Dict] = defaultdict(lambda: {"amounts": [], "dates": [], "category": ""})

    for tx in transactions:
        if tx.amount >= 0:
            continue
        key = tx.description.lower()
        groups[key]["amounts"].append(abs(tx.amount))
        groups[key]["dates"].append(tx.date)
        groups[key]["category"] = tx.category

    subscriptions = []
    for desc, data in groups.items():
        if len(data["amounts"]) < min_occurrences:
            continue

        amounts = data["amounts"]

        # Check if amounts are consistent (within 10% variance)
        avg_amt = sum(amounts) / len(amounts)
        is_consistent = all(
            abs(a - avg_amt) / avg_amt < 0.1 if avg_amt > 0 else True
            for a in amounts
        )

        # Check if they recur monthly-ish
        dates_sorted = sorted(data["dates"])
        is_monthly = False
        if len(dates_sorted) >= 2:
            try:
                d1 = datetime.strptime(dates_sorted[0], "%Y-%m-%d")
                d2 = datetime.strptime(dates_sorted[-1], "%Y-%m-%d")
                total_days = (d2 - d1).days
                expected_intervals = max(1, len(dates_sorted) - 1)
                avg_interval = total_days / expected_intervals
                is_monthly = 25 <= avg_interval <= 35  # roughly monthly
            except ValueError:
                pass

        subscriptions.append({
            "merchant": desc,
            "amount": round(avg_amt, 2),
            "occurrences": len(amounts),
            "total_spent": round(sum(amounts), 2),
            "is_consistent": is_consistent,
            "is_monthly": is_monthly,
            "first_seen": dates_sorted[0],
            "last_seen": dates_sorted[-1],
            "category": data["category"],
            "confidence": "high" if (is_consistent and is_monthly) else "medium" if is_consistent else "low",
        })

    # Sort by total spent (most expensive subscriptions first)
    subscriptions.sort(key=lambda s: s["total_spent"], reverse=True)

    return {"subscriptions": subscriptions}


def spending_summary(
    transactions: List[Transaction],
    period_days: int | None = 30,
) -> Dict:
    """High-level spending summary with alerts for unusual activity.

    Parameters
    ----------
    transactions : All transactions.
    period_days  : Lookback window for "recent" analysis (None = all).
    """
    now = datetime.now()
    cutoff = (now - timedelta(days=period_days)) if period_days else None

    recent = [
        tx for tx in transactions
        if cutoff is None or (tx.date and tx.date >= cutoff.strftime("%Y-%m-%d"))
    ]

    # Basic stats
    total_spent = sum(abs(tx.amount) for tx in transactions if tx.amount < 0)
    total_income = sum(tx.amount for tx in transactions if tx.amount > 0)
    recent_spent = sum(abs(tx.amount) for tx in recent if tx.amount < 0)

    # Largest single transaction
    debits = [tx for tx in transactions if tx.amount < 0]
    largest = max(debits, key=lambda tx: abs(tx.amount)) if debits else None

    # Count unique merchants
    unique_merchants = len(set(tx.description.lower() for tx in transactions))

    # Daily average (over the span of transactions)
    dates = sorted(set(tx.date for tx in transactions if tx.date))
    if len(dates) >= 2:
        d1 = datetime.strptime(dates[0], "%Y-%m-%d")
        d2 = datetime.strptime(dates[-1], "%Y-%m-%d")
        days_span = max(1, (d2 - d1).days)
        daily_avg = round(total_spent / days_span, 2)
    else:
        daily_avg = 0.0

    # Alerts
    alerts = []
    if largest and abs(largest.amount) > 500:
        alerts.append({
            "type": "large_transaction",
            "message": f"Largest single transaction: ${abs(largest.amount):.2f} at {largest.description} on {largest.date}",
            "transaction": largest.to_document_text(),
        })

    # Detect subscriptions
    subs = detect_subscriptions(transactions, min_occurrences=2)
    high_conf_subs = [s for s in subs["subscriptions"] if s["confidence"] == "high"]
    if high_conf_subs:
        alerts.append({
            "type": "subscriptions_found",
            "message": f"Found {len(high_conf_subs)} likely subscriptions totaling ${sum(s['total_spent'] for s in high_conf_subs):.2f}",
            "subscriptions": high_conf_subs,
        })

    return {
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "net": round(total_income - total_spent, 2),
        "recent_spent": round(recent_spent, 2) if period_days else None,
        "period_days": period_days,
        "daily_average": round(daily_avg, 2),
        "transaction_count": len(transactions),
        "unique_merchants": unique_merchants,
        "largest_transaction": {
            "description": largest.description,
            "amount": abs(largest.amount),
            "date": largest.date,
            "category": largest.category,
        } if largest else None,
        "alerts": alerts,
    }
