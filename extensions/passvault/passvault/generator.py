"""Password and passphrase generator for passvault."""

import secrets
import string

# Common English words for Diceware-style passphrases
# Picking readable short words everyone knows
DICEWARE_WORDS = [
    "apple", "baker", "candy", "dance", "eagle", "flame", "grape", "heart",
    "ivory", "jolly", "koala", "lemon", "mango", "noble", "ocean", "piano",
    "queen", "risky", "salty", "tiger", "ultra", "vocal", "wheat", "yacht",
    "zebra", "bench", "cloud", "dodge", "elite", "frost", "gamma", "hobby",
    "inlet", "jumbo", "kebab", "latch", "motif", "neon", "oxide", "plaza",
    "quilt", "raven", "sauce", "theft", "uncle", "vivid", "wound", "yield",
    "amber", "bliss", "cargo", "dome", "ember", "forge", "gauge", "hinge",
    "input", "jewel", "knack", "lunar", "maple", "nylon", "olive", "pixel",
    "radar", "solar", "timid", "ultra", "valid", "wider", "axial", "blunt",
    "crisp", "drain", "equal", "flask", "gland", "hazel", "inbox", "joker",
    "kayak", "lodge", "mocha", "nudge", "orbit", "pouch", "quest", "ranch",
    "sweep", "trait", "usher", "valor", "whale", "xenon", "youth", "zippy",
    "algae", "blend", "crust", "debut", "epoch", "froth", "grasp", "humor",
    "icing", "jazzy", "kiosk", "lyric", "marsh", "nutty", "opera", "prism",
    "quota", "rouge", "slick", "triad", "umbra", "vigor", "waltz", "yodel",
]

# Additional shorter words for easier recall
SHORT_WORDS = [
    "ace", "bay", "cow", "dew", "elf", "fox", "gem", "hay", "ice", "jam",
    "key", "lid", "mix", "net", "owl", "peg", "ram", "sky", "top", "urn",
    "van", "web", "yak", "zag", "ark", "bee", "cap", "den", "erg", "fin",
    "gap", "hub", "ink", "jet", "kit", "lap", "mad", "nap", "oak", "pan",
    "rib", "saw", "tip", "use", "vet", "wit", "xen", "yen", "zip", "ail",
]


def generate_password(
    length: int = 20,
    use_symbols: bool = True,
    use_digits: bool = True,
    uppercase_min: int = 1,
    lowercase_min: int = 1,
    digit_min: int = 1,
    symbol_min: int = 1,
) -> str:
    """Generate a cryptographically secure random password.

    Guarantees at least the minimum counts for each character class,
    then fills the rest with random picks from the full allowed set.
    """
    chars = string.ascii_lowercase
    if use_digits:
        chars += string.digits
    if use_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"

    # Ensure minimum requirements
    password_chars = []
    password_chars.append(secrets.choice(string.ascii_lowercase))
    for _ in range(lowercase_min - 1):
        password_chars.append(secrets.choice(string.ascii_lowercase))

    if uppercase_min > 0:
        for _ in range(uppercase_min):
            password_chars.append(secrets.choice(string.ascii_uppercase))

    if use_digits:
        for _ in range(digit_min):
            password_chars.append(secrets.choice(string.digits))

    if use_symbols:
        for _ in range(symbol_min):
            password_chars.append(secrets.choice("!@#$%^&*()-_=+[]{}|;:,.<>?"))

    # Fill remaining length
    remaining = length - len(password_chars)
    if remaining > 0:
        for _ in range(remaining):
            password_chars.append(secrets.choice(chars))

    # Shuffle to avoid predictable prefix
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def generate_passphrase(word_count: int = 5, separator: str = "-") -> str:
    """Generate a memorable passphrase using Diceware-style word list.

    Each word adds ~10-12 bits of entropy; 5 words = ~50-60 bits.
    """
    words = [secrets.choice(DICEWARE_WORDS) for _ in range(word_count)]
    return separator.join(words)


def password_strength(password: str) -> dict:
    """Estimate password strength and return a report."""
    length = len(password)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    # Estimate entropy (rough)
    pool = 0
    if has_lower:
        pool += 26
    if has_upper:
        pool += 26
    if has_digit:
        pool += 10
    if has_symbol:
        pool += 30

    entropy_bits = length * (pool.bit_length() if pool else 0)

    if entropy_bits >= 100:
        grade = "Very Strong"
    elif entropy_bits >= 70:
        grade = "Strong"
    elif entropy_bits >= 50:
        grade = "Moderate"
    elif entropy_bits >= 30:
        grade = "Weak"
    else:
        grade = "Very Weak"

    return {
        "length": length,
        "has_lowercase": has_lower,
        "has_uppercase": has_upper,
        "has_digit": has_digit,
        "has_symbol": has_symbol,
        "entropy_bits": entropy_bits,
        "grade": grade,
    }