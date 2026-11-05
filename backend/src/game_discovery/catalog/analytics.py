"""Deterministic, version-bound catalog aggregates; never used as assistant evidence."""

import re
import unicodedata
from collections import Counter
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, Field, model_validator

from game_discovery.catalog.contracts import DashboardMetadata, Game, Platform, StrictModel, digest

FORMAT = 'catalog-analytics-v1'
# English function words plus store/game boilerplate; all descriptions are processed.
STOPWORDS = frozenset('''a about above after again against all also am an and any are as at be because been before
being below between both but by can could did do does doing down during each few for from further get had has
have having he her here hers herself him himself his how i if in into is it its itself just me more most my myself
no nor not now of off on once only or other our ours ourselves out over own same she should so some such than
that the their theirs them themselves then there these they this those through to too under until up very was we
were what when where which while who whom why will with would you your yours yourself yourselves game games
play playing player players steam experience new one including features'''.split())
TOKEN = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*", re.UNICODE)
PLATFORMS: tuple[tuple[Platform, str], ...] = (('windows', 'Windows'), ('mac', 'macOS'), ('linux', 'Linux(SteamOS)'))
Count = Annotated[int, Field(ge=0, strict=True)]


class AnalyticsCount(StrictModel):
    label: str = Field(min_length=1, max_length=300)
    count: Count


class AnalyticsCoverage(StrictModel):
    known: Count
    unknown: Count
    invalid: Count = 0


class AnalyticsPlatform(AnalyticsCount):
    unsupported: Count
    unknown: Count


class AnalyticsYear(StrictModel):
    year: int = Field(ge=1, le=9999)
    months: list[Count] = Field(min_length=12, max_length=12)
    unknown_month: Count


class CatalogAnalytics(StrictModel):
    format: Literal['catalog-analytics-v1'] = 'catalog-analytics-v1'
    catalog_version: str = Field(min_length=1, max_length=100)
    observed_from: AwareDatetime | None
    observed_until: AwareDatetime | None
    total_games: Count
    avg_price_cents: float | None = Field(ge=0, allow_inf_nan=False)
    avg_discount_percent: float | None = Field(ge=0, le=100, allow_inf_nan=False)
    total_developers: Count
    coverage: dict[str, AnalyticsCoverage]
    release_years: list[AnalyticsYear] = Field(max_length=1000)
    free_paid: list[AnalyticsCount] = Field(min_length=3, max_length=3)
    price_ranges: list[AnalyticsCount] = Field(min_length=6, max_length=6)
    discount_ranges: list[AnalyticsCount] = Field(min_length=7, max_length=7)
    genres: list[AnalyticsCount] = Field(max_length=15)
    platforms: list[AnalyticsPlatform] = Field(min_length=3, max_length=3)
    developers: list[AnalyticsCount] = Field(max_length=10)
    reviews: list[AnalyticsCount] = Field(max_length=30)
    words: list[AnalyticsCount] = Field(max_length=60)

    @model_validator(mode='after')
    def denominators(self) -> 'CatalogAnalytics':
        total = self.total_games
        required = {'original_price', 'discount', 'developers', 'release_month', 'reviews', 'description', 'genres'}
        if set(self.coverage) != required or any(c.known + c.unknown + c.invalid != total for c in self.coverage.values()):
            raise ValueError('Analytics coverage mismatch')
        if (sum(x.count for x in self.free_paid) != total
                or sum(x.count for x in self.price_ranges) != self.coverage['original_price'].known
                or sum(x.count for x in self.discount_ranges) != self.coverage['discount'].known
                or sum(sum(x.months) for x in self.release_years) != self.coverage['release_month'].known
                or sum(x.count for x in self.reviews) != total
                or any(x.count + x.unsupported + x.unknown != total for x in self.platforms)
                or len({x.year for x in self.release_years}) != len(self.release_years)):
            raise ValueError('Analytics chart denominator mismatch')
        if ((self.avg_price_cents is None) != (self.coverage['original_price'].known == 0)
                or (self.avg_discount_percent is None) != (self.coverage['discount'].known == 0)):
            raise ValueError('Analytics mean denominator mismatch')
        return self


class AnalyticsResponse(StrictModel):
    catalog_version: str
    catalog_created_at: AwareDatetime
    analytics_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    data: CatalogAnalytics


def ranked(counter: Counter[str], limit: int) -> list[AnalyticsCount]:
    return [AnalyticsCount(label=label, count=count) for label, count in sorted(counter.items(), key=lambda x: (-x[1], x[0].casefold(), x[0]))[:limit]]


def build_analytics(games: list[Game], metadata: list[DashboardMetadata], version: str) -> CatalogAnalytics:
    if (len(games) > 2000 or len({g.app_id for g in games}) != len(games)
            or [g.app_id for g in games] != [m.app_id for m in metadata]
            or any(g.eligibility != 'eligible' for g in games)):
        raise ValueError('Analytics requires complete unique eligible game/metadata pairs, max 2000')
    total = len(games)
    prices = [m.original_price_cents for m in metadata if m.original_price_cents is not None]
    discounts = [m.discount_percent for m in metadata if m.discount_percent is not None and 0 <= m.discount_percent <= 100]
    invalid = sum(m.discount_percent is not None and not 0 <= m.discount_percent <= 100 for m in metadata)
    developers: Counter[str] = Counter()
    names: dict[str, str] = {}
    genres: Counter[str] = Counter()
    reviews: Counter[str] = Counter()
    words: Counter[str] = Counter()
    years: dict[int, list[int]] = {}
    unknown_months: Counter[int] = Counter()
    for game, meta in zip(games, metadata, strict=True):
        per_game = set()
        for name in meta.developers or []:
            display = ' '.join(unicodedata.normalize('NFKC', name).split())
            if not display:
                continue
            key = display.casefold()
            names[key] = min(names.get(key, display), display)
            per_game.add(key)
        developers.update(per_game)
        genres.update({genre for genre in game.genres if genre.strip()})
        release = meta.release_date
        if release and release.year is not None:
            months = years.setdefault(release.year, [0] * 12)
            if release.month is not None:
                months[release.month - 1] += 1
            else:
                unknown_months[release.year] += 1
        review = meta.reviews
        reviews['Unknown' if review is None else 'No reviews' if review.total == 0 else review.label or 'Unlabeled reviews'] += 1
        text = unicodedata.normalize('NFKC', game.description).casefold()
        words.update(term for term in TOKEN.findall(text) if 3 <= len(term) <= 24 and term not in STOPWORDS)

    def coverage(known: int, invalid_count: int = 0) -> AnalyticsCoverage:
        return AnalyticsCoverage(known=known, unknown=total-known-invalid_count, invalid=invalid_count)

    def buckets(values: list[int], edges: tuple[int, ...], labels: tuple[str, ...]) -> list[AnalyticsCount]:
        counts = [0] * len(labels)
        for value in values:
            counts[sum(value >= edge for edge in edges)] += 1
        return [AnalyticsCount(label=label, count=count) for label, count in zip(labels, counts, strict=True)]

    dates = [g.observed_at for g in games]
    dates += [e.source.collected_at for m in metadata for e in m.evidence]
    dates += [m.reviews.source.collected_at for m in metadata if m.reviews]
    return CatalogAnalytics(
        catalog_version=version, observed_from=min(dates) if dates else None, observed_until=max(dates) if dates else None,
        total_games=total, avg_price_cents=sum(prices)/len(prices) if prices else None,
        avg_discount_percent=sum(discounts)/len(discounts) if discounts else None, total_developers=len(developers),
        coverage={'original_price': coverage(len(prices)), 'discount': coverage(len(discounts), invalid),
                  'developers': coverage(sum(bool(m.developers and any(n.strip() for n in m.developers)) for m in metadata)),
                  'release_month': coverage(sum(sum(months) for months in years.values())),
                  'reviews': coverage(sum(m.reviews is not None for m in metadata)),
                  'description': coverage(sum(bool(g.description.strip()) for g in games)),
                  'genres': coverage(sum(bool(g.genres) for g in games))},
        release_years=[AnalyticsYear(year=y, months=months, unknown_month=unknown_months[y]) for y, months in sorted(years.items())],
        free_paid=[AnalyticsCount(label=label, count=sum(g.free_to_play is value for g in games))
                   for label, value in [('Free to play', True), ('Paid', False), ('Unknown', None)]],
        price_ranges=buckets(prices, (500, 1000, 2000, 5000, 10000), ('$0–<5', '$5–<10', '$10–<20', '$20–<50', '$50–<100', '$100+')),
        discount_ranges=buckets(discounts, (10, 25, 50, 75, 90, 100), ('0–<10%', '10–<25%', '25–<50%', '50–<75%', '75–<90%', '90–<100%', '100%')),
        genres=ranked(genres, 15),
        platforms=[AnalyticsPlatform(label=label, count=sum(g.platforms.get(key) is True for g in games),
                   unsupported=sum(g.platforms.get(key) is False for g in games), unknown=sum(g.platforms.get(key) is None for g in games))
                   for key, label in PLATFORMS],
        developers=ranked(Counter({names[key]: count for key, count in developers.items()}), 10),
        reviews=ranked(reviews, 30), words=ranked(words, 60))


def validate_analytics(document: dict[str, Any], checksum: str, manifest: dict[str, Any], artifact: dict[str, Any], version: str, count: int) -> CatalogAnalytics:
    if (not all(isinstance(value, dict) for value in (document, manifest, artifact))
            or any(not isinstance(manifest.get(key), str) or re.fullmatch(r'[a-f0-9]{64}', manifest[key]) is None
                   for key in ('games_sha256', 'metadata_sha256', 'artifact_sha256'))):
        raise ValueError('Missing analytics input identity')
    data = CatalogAnalytics.model_validate(document)
    if (data.catalog_version != version or data.total_games != count or digest(document) != checksum
            or manifest.get('sha256') != checksum or manifest.get('catalog_version') != version
            or manifest.get('format') != FORMAT
            or manifest.get('artifact_sha256') != artifact.get('artifact_sha256', digest(artifact))
            or any(manifest.get(key) != artifact.get(key) for key in ('games_sha256', 'metadata_sha256'))):
        raise ValueError('Analytics artifact identity mismatch')
    return data
