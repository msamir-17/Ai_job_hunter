"""
Deterministic cross-source job deduplication service.
Generates canonical dedup_key by normalizing company name, job title, and location.
"""
import hashlib
import re
import unicodedata

# Common legal and corporate suffixes to strip
COMPANY_SUFFIXES = [
    r"\binc\.?\b",
    r"\bllc\.?\b",
    r"\bltd\.?\b",
    r"\bpvt\.?\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bgmbh\b",
    r"\bco\.?\b",
    r"\bholding(s)?\b",
    r"\btechnologies\b",
    r"\btechnology\b",
    r"\bgroup\b",
    r"\bab\b",
]

# Patterns for title suffixes / noise like "- Remote", "(Remote)", "[Full Time]"
TITLE_NOISE = [
    r"\(.*?\)",
    r"\[.*?\]",
    r"-\s*remote\b",
    r"-\s*hybrid\b",
    r"-\s*on-?site\b",
    r"\b(full-?time|part-?time|contract|permanent)\b",
]


def normalize_string(text: str | None) -> str:
    """Lowercases, removes unicode accents, and strips extra spaces."""
    if not text:
        return ""
    # Normalize unicode (e.g., café -> cafe)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    return text


def normalize_company(company: str | None) -> str:
    """Normalizes company names by stripping legal entities and non-alphanumeric chars."""
    comp = normalize_string(company)
    if not comp:
        return ""

    for suffix in COMPANY_SUFFIXES:
        comp = re.sub(suffix, " ", comp, flags=re.IGNORECASE)

    # Remove non-alphanumeric characters except spaces
    comp = re.sub(r"[^\w\s]", " ", comp)
    # Collapse whitespace
    return " ".join(comp.split())


def normalize_title(title: str | None) -> str:
    """Normalizes job titles by removing parenthetical metadata and noise."""
    t = normalize_string(title)
    if not t:
        return ""

    for noise in TITLE_NOISE:
        t = re.sub(noise, " ", t, flags=re.IGNORECASE)

    # Standardize seniorities / abbreviations
    t = re.sub(r"\bsr\.?\b", "senior", t)
    t = re.sub(r"\bjr\.?\b", "junior", t)
    t = re.sub(r"\bmgr\.?\b", "manager", t)
    t = re.sub(r"\beng\.?\b", "engineer", t)
    t = re.sub(r"\bdev\.?\b", "developer", t)

    # Remove non-alphanumeric characters
    t = re.sub(r"[^\w\s]", " ", t)
    return " ".join(t.split())


def normalize_location(location: str | None, is_remote: bool = False) -> str:
    """Normalizes locations; maps remote variations to canonical 'remote'."""
    if is_remote:
        return "remote"

    loc = normalize_string(location)
    if not loc:
        return "unspecified"

    if any(k in loc for k in ["remote", "anywhere", "work from home", "virtual"]):
        return "remote"

    # Remove punctuation and state/country abbreviations if trivial
    loc = re.sub(r"[^\w\s]", " ", loc)
    return " ".join(loc.split())


def generate_dedup_key(
    company: str | None,
    title: str | None,
    location: str | None = None,
    is_remote: bool = False,
) -> str:
    """
    Computes a canonical SHA-256 32-character hex hash based on normalized
    (company, title, location).
    """
    c_norm = normalize_company(company)
    t_norm = normalize_title(title)
    l_norm = normalize_location(location, is_remote=is_remote)

    raw_signature = f"{c_norm}|{t_norm}|{l_norm}".encode("utf-8")
    return hashlib.sha256(raw_signature).hexdigest()[:32]
