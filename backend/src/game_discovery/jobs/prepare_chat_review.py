"""Prepare a method-masked owner review; never invent human judgments.

New output prefixes only. Curated evaluation fixtures only, no live inference.
Keys are separate from the readable worksheet. Relevance uses the frozen rubric.
"""

import argparse
import hashlib
import json
from pathlib import Path

from game_discovery.jobs.chat_evaluation import MANIFEST, METHODS, load_cases, sha256
from game_discovery.jobs.evaluate_chat import save


def label(case_id, method):
    swap = hashlib.sha256(case_id.encode()).digest()[0] % 2
    return ("A", "B")[(METHODS.index(method) + swap) % 2]


def human_summary(review, keys):
    rows = [r for r in review["entries"] if r["split"] == "held_out"]
    if len(rows) != 62 or review.get("owner_confirmation") != "owner_reviewed":
        return {"human_quality_gate": "pending", "reason": "62 held-out method turns and explicit owner review required"}
    required = ("relevance", "factual_claims_total", "unsupported_prose_claims", "false_absence_claims")
    for row in rows:
        if any(type(row[k]) is not int for k in required):
            return {"human_quality_gate": "pending", "reason": "missing owner judgments"}
        if row["relevance"] not in (0, 1, 2) or not 0 <= row["false_absence_claims"] <= row["unsupported_prose_claims"] <= row["factual_claims_total"]:
            raise ValueError("invalid_human_judgment")
    summary = {}
    recalls = {method: [] for method in METHODS}
    pairs = {}
    for row in rows:
        pairs.setdefault((row["case_id"], row["turn"]), []).append(row)
    for pair in pairs.values():
        if len(pair) != 2 or not all(r.get("catalog_labels_exhaustive") is True for r in pair):
            continue
        relevant = pair[0].get("relevant_catalog_ids")
        if (not isinstance(relevant, list) or any(type(i) is not int for i in relevant)
                or set(relevant) != set(pair[1].get("relevant_catalog_ids") or [])):
            raise ValueError("paired_exhaustive_relevance_labels_required")
        if relevant:
            for row in pair:
                recalls[keys[row["review_id"]]].append(len(set(row["retrieved_ids"][:8]) & set(relevant)) / len(set(relevant)))
    for method in METHODS:
        chosen = [r for r in rows if keys[r["review_id"]] == method]
        if len(chosen) != 31 or len({(r["case_id"], r["turn"]) for r in chosen}) != 31:
            raise ValueError("paired_review_inventory_mismatch")
        claims = sum(r["factual_claims_total"] for r in chosen)
        unsupported = sum(r["unsupported_prose_claims"] for r in chosen)
        summary[method] = {"mean_relevance": sum(r["relevance"] for r in chosen) / len(chosen),
                           "unsupported_claims": unsupported, "factual_claims": claims,
                           "unsupported_rate": unsupported / claims if claims else None,
                           "recall_at_8": sum(recalls[method]) / len(recalls[method]) if recalls[method] else None,
                           "recall_judged_pairs": len(recalls[method]),
                           "false_absence_claims": sum(r["false_absence_claims"] for r in chosen)}
    left, right = (summary[m] for m in METHODS)
    # Zero factual units means no unsupported units observed; undefined rates
    # remain null in the report rather than being presented as measured zeros.
    nonregression = left["mean_relevance"] >= right["mean_relevance"] and (
        (left["unsupported_rate"] or 0) <= (right["unsupported_rate"] or 0))
    return {"human_quality_gate": "pass" if nonregression else "fail", "methods": summary,
            "scope": "human nonregression only; not whole R4 acceptance, latency or mandatory behavior gates"}


def prepare(source, prefix):
    outputs = [prefix.with_suffix(suffix) for suffix in (".json", ".md", ".keys.json")]
    if any(p.exists() for p in outputs) or not prefix.parent.is_dir():
        raise ValueError("new_prefix_in_existing_directory_required")
    report = json.loads(source.read_text(encoding="utf-8"))
    frozen = {c["id"]: c for c in load_cases()}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    review = {"schema_version": 1, "source_sha256": sha256(source), "source_status": report["status"],
              "owner_confirmation": None, "rubric": manifest["rubric"],
              "catalog_evidence": report["catalog_evidence"], "entries": []}
    keys = {}
    markdown = ["# R4 owner review — unscored worksheet", "",
        "Source status: **" + report["status"] + "**. Only recorded outputs appear below; missing turns are not a pass.", "",
        "Rate relevance **0** irrelevant/incorrect, **1** partly useful with material missing fit/scope, **2** useful/relevant/correctly scoped.",
        "Inspect all factual prose, including backend notes; count factual units, unsupported units and false-absence claims. Subjective claims need qualifications.",
        "Enter ratings in the companion JSON and set owner_confirmation to owner_reviewed only after your review. Blank/null means unjudged, never zero.",
        "Catalog facts below are dated records, not live Steam facts. The JSON contains full canonical evidence once for checking claims.",
        "For Recall@8, relevant_catalog_ids must be exhaustive human labels over the eligible catalog; anchor seeds are insufficient. Leave null if not reviewed.", ""]
    for record in sorted(report["records"], key=lambda r: (r["case_id"], r["turn"], label(r["case_id"], r["method"]))):
        case = frozen[record["case_id"]]
        display = label(case["id"], record["method"])
        review_id = f'{case["id"]}:{record["turn"]}:{display}'
        keys[review_id] = record["method"]
        response = record.get("response", {})
        entry = {"review_id": review_id, "case_id": case["id"], "turn": record["turn"], "split": case["split"],
                 "response_label": display, "execution_status": record["status"], "user": record["user"],
                 "conversation_user_turns": [t["user"] for t in case["turns"][:record["turn"]]],
                 "message": response.get("message"), "games": response.get("games", []),
                 "retrieved_ids": record.get("ranked_ids", []), "generation_evidence_ids": record.get("generation_evidence_ids", []),
                 "relevance": None, "factual_claims_total": None, "unsupported_prose_claims": None,
                 "false_absence_claims": None, "notes": "", "relevant_catalog_ids": None, "catalog_labels_exhaustive": False}
        entry["raw_generated_answers"] = [a["output"] for a in report["provider_attempts"]
            if a["case_id"] == case["id"] and a["turn"] == record["turn"] and a["method"] == record["method"]
            and a["stage"] == "generate" and "output" in a]
        review["entries"].append(entry)
        markdown += [f'## {review_id} ({case["split"]})', "", "**Conversation requests:** " + " → ".join(entry["conversation_user_turns"]),
                     "", "**Response:** " + (entry["message"] or "No delivered answer — " + record["status"]), "",
                     "**Selected catalog cards:**"]
        if record["status"] != "ok":
            markdown += ["", "**Rejected model prose — not delivered to the user:**"]
            markdown += [answer.get("message", "No generated prose recorded.") for answer in entry["raw_generated_answers"]]
        for card in entry["games"]:
            game = review["catalog_evidence"][str(card["app_id"])]
            markdown.append(f'- {game["app_id"]}: **{game["title"]}**; modes: {", ".join(game["modes"]) or "not recorded"}; '
                            f'platforms: {json.dumps(game["platforms"])}. {game["description"][:300]}')
        markdown += ["", "Relevance: ___ /2 · factual units: ___ · unsupported: ___ · false absence: ___", "Notes: ___", ""]
    save(outputs[0], review)
    save(outputs[2], keys)
    outputs[1].write_text("\n".join(markdown), encoding="utf-8")
    print(json.dumps({"status": "unscored_owner_review_prepared", "entries": len(review["entries"]),
                      "human_ratings": 0, "source_status": report["status"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-prefix", type=Path)
    parser.add_argument("--score", type=Path)
    parser.add_argument("--keys", type=Path)
    args = parser.parse_args()
    if args.score:
        if not args.keys or args.source or args.output_prefix:
            parser.error("--score requires --keys and no prepare arguments")
        print(json.dumps(human_summary(json.loads(args.score.read_text(encoding="utf-8")),
                                      json.loads(args.keys.read_text(encoding="utf-8")))))
    else:
        if not args.source or not args.output_prefix or args.keys:
            parser.error("prepare requires --source and a new --output-prefix")
        prepare(args.source, args.output_prefix)


if __name__ == "__main__":
    main()
