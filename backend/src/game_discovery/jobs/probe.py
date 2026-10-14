"""Bounded source experiment, not a production collection or eligibility pipeline."""

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from game_discovery.jobs.audit import steam_app_id
from game_discovery.catalog.eligibility import classify_appdetails


def identity_matches(requested_id: int, canonical_url: str | None) -> bool:
    return canonical_url is not None and steam_app_id(canonical_url) == requested_id


def verified_review_summary(payload: dict, app_identity_verified: bool) -> dict | None:
    # The reviews endpoint can return success=1 and zero counts for nonexistent IDs.
    # A successful aggregate response is not proof that the game exists.
    summary = payload.get("query_summary")
    if not app_identity_verified or payload.get("success") != 1 or not isinstance(summary, dict):
        return None
    counts = [summary.get(key) for key in ("total_positive", "total_negative", "total_reviews")]
    if any(type(value) is not int or value < 0 for value in counts) or counts[0] + counts[1] != counts[2]:
        return None
    return summary


def run_probe(app_ids: list[int], output_dir: Path, reviews: bool = False) -> int:
    if not 1 <= len(app_ids) <= 5 or any(app_id <= 0 for app_id in app_ids):
        raise ValueError("Probe requires 1–5 positive Steam app IDs")
    from scrapling.fetchers import Fetcher

    output_dir.mkdir(parents=True, exist_ok=True)
    observations = []
    for app_id in app_ids:
        app_identity_verified = False
        urls = {
            "appdetails": f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=us&l=english",
            "store_page": f"https://store.steampowered.com/app/{app_id}/?cc=us&l=english",
        }
        if reviews:
            urls["reviews"] = f"https://store.steampowered.com/appreviews/{app_id}?json=1&filter=all&language=all&purchase_type=all&num_per_page=0"
        for source, url in urls.items():
            started = time.perf_counter()
            observation = {"app_id": app_id, "source": source, "url": url,
                           "collected_at": datetime.now(UTC).isoformat(), "requested_region": "US"}
            try:
                if source in {"appdetails", "reviews"}:
                    request = Request(url, headers={"User-Agent": "GameDiscoveryFeasibility/0.1"})
                    with urlopen(request, timeout=20) as response:
                        body = response.read(2 * 1024 * 1024 + 1)
                        observation["status"] = response.status
                    if len(body) > 2 * 1024 * 1024:
                        raise ValueError("Response exceeds probe size bound")
                    payload = json.loads(body)
                    if source == "reviews":
                        observation["success"] = payload.get("success") == 1
                        summary = verified_review_summary(payload, app_identity_verified)
                        observation["identity_verified"] = summary is not None
                        observation["identity_basis"] = "preceding_appdetails_identity_and_reviews_endpoint_url"
                        observation["query_summary"] = summary
                        observation["scope"] = {"language": "all", "purchase_type": "all", "filter": "all"}
                        observation["individual_reviews_returned"] = len(payload.get("reviews", []))
                    else:
                        envelope = payload[str(app_id)]
                        observation["success"] = envelope.get("success", False)
                        data = envelope.get("data", {})
                        observation["identity_verified"] = data.get("steam_appid") == app_id
                        app_identity_verified = observation["identity_verified"]
                        observation["available_fields"] = sorted(data)
                        observation["facts"] = {key: data.get(key) for key in (
                            "steam_appid", "name", "type", "is_free", "platforms", "price_overview",
                            "release_date", "categories", "genres", "content_descriptors")}
                        observation["classification"] = classify_appdetails(data)
                else:
                    page = Fetcher.get(url, timeout=20, retries=0)
                    body = page.body
                    observation["status"] = page.status
                    observation["title"] = page.css("title::text").get()
                    canonical = page.css('link[rel="canonical"]::attr(href)').get()
                    observation["canonical_url"] = canonical
                    observation["identity_verified"] = identity_matches(app_id, canonical)
                    observation["tag_labels"] = [text.strip() for text in page.css("a.app_tag::text").getall() if text.strip()]
                    observation["has_description"] = bool(page.css(".game_description_snippet"))
                    observation["age_gate"] = bool(page.css("#agecheck_form"))
                    observation["early_access_banner"] = bool(page.css(".early_access_header"))
                filename = f"{app_id}-{source}.{'html' if source == 'store_page' else 'json'}"
                (output_dir / filename).write_bytes(body)
                observation.update(snapshot=filename, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
                observation["error_type"] = type(error).__name__
            except Exception as error:
                # Fetcher transport errors have provider-specific exception types.
                observation["error_type"] = type(error).__name__
            observation["elapsed_seconds"] = round(time.perf_counter() - started, 4)
            observations.append(observation)
            time.sleep(2)
    report = {"schema_version": 1, "purpose": "M0 source feasibility only",
              "observations": observations}
    (output_dir / "manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    failed = any(item.get("error_type") or item.get("status") != 200
                 or not item.get("identity_verified") for item in observations)
    print(json.dumps({"job": "probe", "status": "partial" if failed else "ok",
                      "report": str(output_dir / "manifest.json"), "requests": len(observations)}))
    return 1 if failed else 0
