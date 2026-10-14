"""Conservative source classification; absent facts never imply eligibility."""


def classify_appdetails(data: dict) -> dict:
    app_type = data.get("type")
    genres = data.get("genres")
    early_access = None
    if isinstance(genres, list):
        early_access = any(isinstance(term, dict) and str(term.get("id")) == "70" for term in genres)
    result = {"status": "quarantined", "reason": "missing_type", "early_access": early_access}
    if not isinstance(app_type, str) or not app_type:
        return result
    if app_type != "game":
        return {**result, "status": "excluded", "reason": f"non_game_type:{app_type}"}
    release = data.get("release_date")
    if not isinstance(release, dict) or not isinstance(release.get("coming_soon"), bool):
        return {**result, "reason": "missing_release_status"}
    if release["coming_soon"]:
        return {**result, "status": "excluded", "reason": "unreleased"}
    descriptors = data.get("content_descriptors")
    ids = descriptors.get("ids") if isinstance(descriptors, dict) else None
    if not isinstance(ids, list) or any(type(value) is not int for value in ids):
        return {**result, "reason": "missing_content_classification"}
    # Steam content descriptor IDs: 3 Adult Only Sexual Content;
    # 4 Gratuitous Sexual Content. Ordinary mature/violence/nudity descriptors
    # are not blanket exclusions. The source mapping is documented in M0 evidence.
    if set(ids) & {3, 4}:
        return {**result, "status": "excluded", "reason": "adult_only_sexual_content"}
    if any(value not in {1, 2, 3, 4, 5} for value in ids):
        return {**result, "reason": "unknown_content_descriptor"}
    return {**result, "status": "eligible", "reason": "released_game_with_content_classification"}
