"""Canceller — Generate cancellation info for known services."""

from src.merchant_db import get_cancellation_for, list_known_merchants


def get_cancellation_info(service_name: str) -> str:
    """Return cancellation URL and process for a known service."""
    info = get_cancellation_for(service_name)
    if not info:
        return (
            f"Cancellation information not found for '{service_name}'.\n"
            f"Known services: {', '.join(list_known_merchants())}"
        )

    lines = [
        f"── Cancel {info['name']} ──",
        f"  Category:     {info['category']}",
        f"  Price:        ${info['typical_price']:.2f}/{info['frequency']}",
        f"  URL:          {info['cancellation_url']}",
        f"  Process:      {info['cancellation_process']}",
    ]
    if info.get("notes"):
        lines.append(f"  Notes:        {info['notes']}")
    return "\n".join(lines)


def batch_cancellation_info(service_names: list[str]) -> str:
    """Get cancellation info for multiple services."""
    results: list[str] = []
    for name in service_names:
        results.append(get_cancellation_info(name))
    return "\n\n".join(results)