from __future__ import annotations

from typing import Iterable


def comma_separated(values: Iterable[str]) -> str:
    return ", ".join(values)


def slugify_name(name: str) -> str:
    # simple slug: lowercase, alnum and hyphens
    import re
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug or "table"


