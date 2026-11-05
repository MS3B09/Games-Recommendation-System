"""Dashboard source normalization, separate from stable discovery documents."""

import re
from datetime import datetime

from game_discovery.catalog.contracts import DashboardMetadata, Evidence, ReleaseDate, ReviewSummary, Source


def release_date(raw: str) -> ReleaseDate:
    for pattern, precision in (('%b %d, %Y', 'day'), ('%d %b, %Y', 'day'),
                               ('%b %Y', 'month'), ('%B %Y', 'month'), ('%Y', 'year')):
        try:
            parsed = datetime.strptime(raw, pattern)
        except ValueError:
            continue
        return ReleaseDate(raw=raw, precision=precision, year=parsed.year,
                           month=parsed.month if precision != 'year' else None,
                           day=parsed.day if precision == 'day' else None)
    return ReleaseDate(raw=raw, precision='unknown')


def normalize_metadata(app_id: int, data: dict, source: Source,
                       review_payload: dict | None = None, review_source: Source | None = None) -> DashboardMetadata:
    evidence = []

    def record(field, value):
        if value is not None:
            evidence.append(Evidence(id=f'{app_id}:metadata:{field}', field=field, value=value, source=source))
        return value

    developers = data.get('developers')
    if isinstance(developers, list) and all(isinstance(name, str) and name.strip() for name in developers):
        developers = list(dict.fromkeys(re.sub(r'\s+', ' ', name).strip() for name in developers)) or None
    else:
        developers = None
    raw_date = data.get('release_date', {}).get('date')
    released = release_date(record('release_date_raw', raw_date)) if isinstance(raw_date, str) and len(raw_date) <= 100 else None
    price = data.get('price_overview') or {}
    initial = price.get('initial')
    initial = initial if price.get('currency') == 'USD' and type(initial) is int and 0 <= initial <= 2147483647 else None
    discount = price.get('discount_percent')
    discount = discount if type(discount) is int else None
    reviews = None
    if review_payload is not None and review_source is not None:
        label = review_payload.get('review_score_desc')
        reviews = ReviewSummary(label=label if isinstance(label, str) else None,
                                positive=review_payload['total_positive'], negative=review_payload['total_negative'],
                                total=review_payload['total_reviews'], source=review_source)
    return DashboardMetadata(app_id=app_id, developers=record('developers', developers), release_date=released,
                             original_price_cents=record('original_price_cents', initial),
                             discount_percent=record('discount_percent', discount), reviews=reviews, evidence=evidence)
