from __future__ import annotations

import re
from urllib.parse import urlparse

from .errors import ValidationError

_USERNAME = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


def parse_username(value: str) -> str:
    raw = value.strip()
    if raw.startswith("https://github.com/") or raw.startswith("http://github.com/"):
        raw = urlparse(raw).path.strip("/").split("/")[0]
    raw = raw.lstrip("@").strip("/")
    if not raw or not _USERNAME.fullmatch(raw):
        raise ValidationError("Enter a valid GitHub username or github.com/username URL.")
    return raw


def parse_repo(value: str) -> tuple[str, str]:
    raw = value.strip()
    if not raw:
        raise ValidationError("A repository URL is required.")

    if "://" in raw or raw.startswith("github.com/") or raw.startswith("www.github.com/"):
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if parsed.hostname not in {"github.com", "www.github.com"}:
            raise ValidationError("Only github.com repository URLs are accepted.")
        parts = [part for part in parsed.path.split("/") if part]
    else:
        parts = [part for part in raw.split("/") if part]

    if len(parts) < 2:
        raise ValidationError("Repository URL must include an owner and a repository name.")
    if any(part in {".", ".."} for part in parts):
        raise ValidationError("Repository URL contains a traversal segment.")

    owner, repo = parts[0], parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not _SEGMENT.fullmatch(owner) or not _SEGMENT.fullmatch(repo):
        raise ValidationError("Repository owner or name contains unsupported characters.")
    return owner, repo


def parse_pagination(page: int, per_page: int, maximum: int = 100) -> tuple[int, int]:
    if page < 1 or page > 1000:
        raise ValidationError("Page must be between 1 and 1000.")
    if per_page < 1 or per_page > maximum:
        raise ValidationError(f"Per page must be between 1 and {maximum}.")
    return page, per_page
