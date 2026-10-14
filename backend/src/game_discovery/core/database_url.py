"""Credential-safe URL handling shared by application and developer jobs."""

from urllib.parse import urlsplit


def normalize_db_url(value: str) -> str:
    value = value.replace("postgresql+psycopg://", "postgresql://", 1)
    parsed = urlsplit(value)
    if parsed.netloc.count("@") > 1:
        credentials, host = parsed.netloc.rsplit("@", 1)
        value = parsed._replace(netloc=f"{credentials.replace('@', '%40')}@{host}").geturl()
    return value


def db_url_matches_project(value: str | None, project_url: str) -> bool:
    if not value:
        return False
    try:
        reference = (urlsplit(project_url).hostname or "").removesuffix(".supabase.co")
        parsed = urlsplit(normalize_db_url(value))
        if parsed.scheme not in {"postgres", "postgresql"} or parsed.netloc.count("@") > 1:
            return False
        _ = parsed.port
        return bool(reference) and (
            parsed.hostname == f"db.{reference}.supabase.co"
            or ((parsed.hostname or "").endswith(".pooler.supabase.com")
                and (parsed.username or "").endswith(f".{reference}"))
        )
    except ValueError:
        return False


def role_identity(value: str, project_url: str) -> str | None:
    parsed = urlsplit(normalize_db_url(value))
    username = parsed.username
    reference = (urlsplit(project_url).hostname or "").removesuffix(".supabase.co")
    if username and (parsed.hostname or "").endswith(".pooler.supabase.com"):
        username = username.removesuffix(f".{reference}")
    return username
