GOOGLE_PROVIDERS = {
    "google", "gmail", "google drive", "drive",
    "google sheets", "sheets", "google calendar", "calendar",
    "google docs", "docs", "google_oauth"
}


def normalize_provider(provider: str) -> str:
    """Normalizes all Google sub-services (Gmail, Drive, Sheets, etc.) to the unified 'Google' provider."""
    if not provider:
        return "Generic"
    p_clean = provider.strip().lower()
    if p_clean in GOOGLE_PROVIDERS:
        return "Google"
    return provider.capitalize()
