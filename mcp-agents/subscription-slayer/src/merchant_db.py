"""Known subscription merchants database.

Maps merchant names to metadata: category, typical price, cancellation details.
"""

from dataclasses import dataclass, field
from typing import Optional

from src.models import Category, Frequency


@dataclass
class MerchantInfo:
    """Known information about a subscription merchant."""

    name: str
    category: Category
    typical_price: float
    frequency: Frequency = Frequency.MONTHLY
    aliases: list[str] = field(default_factory=list)
    cancellation_url: str = ""
    cancellation_process: str = ""
    notes: str = ""


# 20+ known subscription merchants
MERCHANT_DB: dict[str, MerchantInfo] = {
    merchant.name.lower(): merchant
    for merchant in [
        MerchantInfo(
            name="Spotify",
            category=Category.MUSIC,
            typical_price=10.99,
            aliases=["spotify premium", "spotify usa", "spotify family"],
            cancellation_url="https://www.spotify.com/account/subscription/",
            cancellation_process="Go to Account > Subscription > Cancel Subscription. Can also manage via account page.",
            notes="Premium Individual $10.99/mo, Family $16.99/mo, Duo $14.99/mo",
        ),
        MerchantInfo(
            name="Netflix",
            category=Category.STREAMING,
            typical_price=15.49,
            aliases=["netflix", "netflix usa", "netflix.com"],
            cancellation_url="https://www.netflix.com/YourAccount",
            cancellation_process="Account > Cancel Membership. Confirm cancellation. Access continues until end of billing period.",
            notes="Standard with ads $6.99, Standard $15.49, Premium $22.99/mo",
        ),
        MerchantInfo(
            name="Disney+",
            category=Category.STREAMING,
            typical_price=7.99,
            aliases=["disney plus", "disney+", "disneyplus", "disney streaming"],
            cancellation_url="https://www.disneyplus.com/account/subscription",
            cancellation_process="Account > Subscription > Cancel. Confirm. Access until end of billing period.",
            notes="$7.99/mo or $79.99/yr. Can bundle with Hulu/ESPN+.",
        ),
        MerchantInfo(
            name="Hulu",
            category=Category.STREAMING,
            typical_price=7.99,
            aliases=["hulu", "hulu.com"],
            cancellation_url="https://www.hulu.com/account",
            cancellation_process="Account > Cancel > Confirm. If on promo, price may increase after cancellation window.",
            notes="Ad-supported $7.99, No ads $14.99, +Live TV from $75.99/mo",
        ),
        MerchantInfo(
            name="HBO Max",
            category=Category.STREAMING,
            typical_price=15.99,
            aliases=["hbo max", "max", "hbomax", "hbomax.com", "warner bros"],
            cancellation_url="https://www.max.com/account",
            cancellation_process="Account > Manage Subscription > Cancel. Confirm by clicking Cancel Subscription.",
            notes="With ads $9.99, Ad-free $15.99, Ultimate $19.99/mo",
        ),
        MerchantInfo(
            name="Apple Music",
            category=Category.MUSIC,
            typical_price=10.99,
            aliases=["apple music", "music.apple.com", "itunes match"],
            cancellation_url="https://music.apple.com/subscribe",
            cancellation_process="Settings > [your name] > Subscriptions > Apple Music > Cancel Subscription. Requires Apple ID.",
            notes="Individual $10.99, Family $16.99, Student $5.99/mo",
        ),
        MerchantInfo(
            name="Amazon Prime",
            category=Category.STREAMING,
            typical_price=14.99,
            frequency=Frequency.MONTHLY,
            aliases=["amazon prime", "prime video", "amazon.com/prime", "amazon digital"],
            cancellation_url="https://www.amazon.com/gp/help/customer/display.html?nodeId=201910370",
            cancellation_process="Account > Prime > Manage Membership > End Membership. Access until end of paid period.",
            notes="$14.99/mo or $139/yr. Includes video, music, shipping, photo storage.",
        ),
        MerchantInfo(
            name="YouTube Premium",
            category=Category.MUSIC,
            typical_price=11.99,
            aliases=["youtube premium", "yt premium", "youtube music", "youtube red"],
            cancellation_url="https://www.youtube.com/premium",
            cancellation_process="Profile picture > Paid memberships > Manage > Cancel. Confirm cancellation.",
            notes="$11.99/mo individual, $17.99/mo family. Includes YouTube Music.",
        ),
        MerchantInfo(
            name="Patreon",
            category=Category.OTHER,
            typical_price=5.00,
            aliases=["patreon", "patreon.com"],
            cancellation_url="https://www.patreon.com/settings/memberships",
            cancellation_process="Settings > Memberships > Manage next to creator > Edit > Cancel pledge.",
            notes="Varies by creator. Average $5-10/mo per creator pledged.",
        ),
        MerchantInfo(
            name="Medium",
            category=Category.NEWS,
            typical_price=5.00,
            aliases=["medium", "medium.com", "medium membership"],
            cancellation_url="https://medium.com/me/settings/subscription",
            cancellation_process="Settings > Membership > Manage > Cancel. Access until end of billing period.",
            notes="$5/mo or $50/yr. Unlimited reads on Medium.",
        ),
        MerchantInfo(
            name="New York Times",
            category=Category.NEWS,
            typical_price=4.00,
            frequency=Frequency.WEEKLY,
            aliases=["nytimes", "ny times", "new york times", "nytimes.com"],
            cancellation_url="https://www.nytimes.com/account/cancel",
            cancellation_process="Account > Cancel Subscription. May need to go through retention offers (chat/phone).",
            notes="Typically $4/week introductory, then $8-17/week. Digital only or All Access.",
        ),
        MerchantInfo(
            name="Dropbox",
            category=Category.CLOUD,
            typical_price=11.99,
            aliases=["dropbox", "dropbox.com"],
            cancellation_url="https://www.dropbox.com/account/plan",
            cancellation_process="Settings > Plan > Cancel. Confirm. Downgrade to free at end of billing period.",
            notes="Plus $9.99/mo billed yearly ($119.88/yr), $11.99/mo monthly. Family $19.99/mo.",
        ),
        MerchantInfo(
            name="Google Drive",
            category=Category.CLOUD,
            typical_price=1.99,
            aliases=["google drive", "google one", "google storage", "google workspace"],
            cancellation_url="https://one.google.com/cancel",
            cancellation_process="Google One > Settings > Manage membership > Cancel. Downgrades at end of billing period.",
            notes="100GB $1.99/mo, 200GB $2.99/mo, 2TB $9.99/mo",
        ),
        MerchantInfo(
            name="iCloud+",
            category=Category.CLOUD,
            typical_price=0.99,
            aliases=["icloud", "icloud+", "apple icloud", "apple storage"],
            cancellation_url="https://support.apple.com/en-us/HT201304",
            cancellation_process="Settings > [your name] > iCloud > Manage Storage > Change Storage Plan > Downgrade to Free.",
            notes="50GB $0.99, 200GB $2.99, 2TB $9.99/mo",
        ),
        MerchantInfo(
            name="Adobe Creative Cloud",
            category=Category.SOFTWARE,
            typical_price=54.99,
            aliases=["adobe cc", "adobe creative cloud", "adobe photoshop", "adobe", "adobe.com"],
            cancellation_url="https://account.adobe.com/plans",
            cancellation_process="Account > Manage Plan > Cancel. Adobe charges early termination fee (50% of remaining contract) for annual plans.",
            notes="Photography $9.99/mo, All Apps $54.99/mo. Annual commitment with early termination fee.",
        ),
        MerchantInfo(
            name="Microsoft 365",
            category=Category.SOFTWARE,
            typical_price=6.99,
            aliases=["office 365", "microsoft 365", "microsoft office", "ms office"],
            cancellation_url="https://account.microsoft.com/services",
            cancellation_process="Account > Services & subscriptions > Manage > Cancel. Access until end of billing period.",
            notes="Personal $6.99/mo or $69.99/yr. Family $9.99/mo or $99.99/yr.",
        ),
        MerchantInfo(
            name="Canva Pro",
            category=Category.SOFTWARE,
            typical_price=12.99,
            aliases=["canva", "canva pro", "canva.com", "canva team"],
            cancellation_url="https://www.canva.com/account/billing",
            cancellation_process="Account > Billing > Plans > Cancel subscription. Access until end of billing period.",
            notes="$12.99/mo or $119.99/yr. Team $14.99/mo per person (3-min).",
        ),
        MerchantInfo(
            name="Headspace",
            category=Category.FITNESS,
            typical_price=12.99,
            aliases=["headspace", "headspace.com"],
            cancellation_url="https://www.headspace.com/account-settings",
            cancellation_process="Account > Settings > Subscription > Cancel. May need to re-cancel through app store if subscribed via iOS/Android.",
            notes="$12.99/mo or $69.99/yr. Family plan available.",
        ),
        MerchantInfo(
            name="Calm",
            category=Category.FITNESS,
            typical_price=14.99,
            aliases=["calm", "calm.com"],
            cancellation_url="https://www.calm.com/settings/subscription",
            cancellation_process="Settings > Subscription > Cancel. Paid through app store? Manage there instead.",
            notes="$14.99/mo or $69.99/yr. Lifetime available for $399.99.",
        ),
        MerchantInfo(
            name="Duolingo Plus",
            category=Category.EDUCATION,
            typical_price=6.99,
            aliases=["duolingo", "duolingo plus", "duolingo super", "duolingo.com"],
            cancellation_url="https://www.duolingo.com/settings/subscription",
            cancellation_process="Settings > Subscription > Manage > Cancel. If via app store, manage subscription there.",
            notes="$6.99/mo or $83.99/yr. Super Duolingo renamed from Plus.",
        ),
        MerchantInfo(
            name="Peloton",
            category=Category.FITNESS,
            typical_price=44.00,
            aliases=["peloton", "peloton app", "onepeloton", "peloton.com"],
            cancellation_url="https://www.onepeloton.com/cancel",
            cancellation_process="Account > Membership > Cancel. Can also email support@onepeloton.com.",
            notes="App membership $12.99/mo. All-Access $44/mo (required for Peloton hardware).",
        ),
        MerchantInfo(
            name="ClassPass",
            category=Category.FITNESS,
            typical_price=49.00,
            aliases=["classpass", "classpass.com"],
            cancellation_url="https://classpass.com/account/membership",
            cancellation_process="Account > Membership > Cancel Membership. Credits expire if not used.",
            notes="Starting at $49/mo for 10 credits. Varies by city.",
        ),
        MerchantInfo(
            name="Planet Fitness",
            category=Category.FITNESS,
            typical_price=10.00,
            aliases=["planet fitness", "pf", "planetfitness"],
            cancellation_url="https://www.planetfitness.com/",
            cancellation_process="Must cancel in-person at home club or send certified mail. Cannot cancel online.",
            notes="$10/mo classic, $24.99/mo black card. Annual fee $39 once per year.",
        ),
        MerchantInfo(
            name="Crunch Fitness",
            category=Category.FITNESS,
            typical_price=9.99,
            aliases=["crunch fitness", "crunch", "crunch gym"],
            cancellation_url="https://www.crunch.com/",
            cancellation_process="Must cancel in-person. Some locations allow email cancellation. 30-day notice required.",
            notes="$9.99/mo base. Annual fee varies by location.",
        ),
    ]
}

# Build alias lookup
ALIAS_MAP: dict[str, str] = {}
for merchant_name, info in MERCHANT_DB.items():
    for alias in info.aliases:
        ALIAS_MAP[alias] = merchant_name
    ALIAS_MAP[merchant_name] = merchant_name


def resolve_merchant(description: str) -> tuple[Optional[str], Optional[MerchantInfo]]:
    """Resolve a transaction description to a known merchant.

    Returns (canonical_name, merchant_info) or (None, None) if unknown.
    """
    desc_lower = description.lower().strip()

    # Direct match
    if desc_lower in ALIAS_MAP:
        name = ALIAS_MAP[desc_lower]
        return name, MERCHANT_DB[name]

    # Substring matching
    for alias, canonical_name in ALIAS_MAP.items():
        if alias in desc_lower or desc_lower in alias:
            return canonical_name, MERCHANT_DB[canonical_name]

    return None, None


def get_cancellation_for(service_name: str) -> Optional[dict]:
    """Get cancellation details for a known service."""
    name_lower = service_name.lower().strip()
    info = MERCHANT_DB.get(name_lower)
    if info:
        return {
            "name": info.name,
            "category": info.category.value,
            "typical_price": info.typical_price,
            "frequency": info.frequency.value,
            "cancellation_url": info.cancellation_url,
            "cancellation_process": info.cancellation_process,
            "notes": info.notes,
        }

    # Try alias lookup
    canonical = ALIAS_MAP.get(name_lower)
    if canonical and canonical != name_lower:
        info = MERCHANT_DB[canonical]
        return {
            "name": info.name,
            "category": info.category.value,
            "typical_price": info.typical_price,
            "frequency": info.frequency.value,
            "cancellation_url": info.cancellation_url,
            "cancellation_process": info.cancellation_process,
            "notes": info.notes,
        }
    return None


def list_known_merchants() -> list[str]:
    """Return all known merchant names."""
    return sorted(MERCHANT_DB.keys())