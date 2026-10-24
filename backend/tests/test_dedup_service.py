import pytest
from app.services.dedup_service import (
    generate_dedup_key,
    normalize_company,
    normalize_location,
    normalize_title,
)


def test_normalize_company():
    assert normalize_company("Stripe, Inc.") == "stripe"
    assert normalize_company("Spotify AB LLC") == "spotify"
    assert normalize_company("Datadog Technologies Corp.") == "datadog"
    assert normalize_company("Canonical Ltd.") == "canonical"


def test_normalize_title():
    assert normalize_title("Senior Python Developer - Remote") == "senior python developer"
    assert normalize_title("Sr. Software Eng. (Backend)") == "senior software engineer"
    assert normalize_title("Staff Dev [Full-Time]") == "staff developer"


def test_normalize_location():
    assert normalize_location("Remote, US") == "remote"
    assert normalize_location("San Francisco, CA", is_remote=True) == "remote"
    assert normalize_location("New York, NY") == "new york ny"


def test_generate_dedup_key_deterministic_and_unique():
    key1 = generate_dedup_key("Stripe, Inc.", "Senior Backend Engineer - Remote", "Remote, US")
    key2 = generate_dedup_key("Stripe", "Sr. Backend Eng", is_remote=True)
    assert key1 == key2
    assert len(key1) == 32

    key3 = generate_dedup_key("Spotify", "Product Manager", "Stockholm")
    assert key1 != key3
