"""Freeze/check R0 design artifacts, NOT a retrieval or answer evaluator."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from contracts import ChatStateV2, RetrievalOutcome, TurnPlan

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/evaluation/chat-rag.jsonl"
MANIFEST = ROOT / "data/evaluation/chat-rag-manifest.json"
SCHEMAS = ROOT / "docs/reports/conversational-rag-r0-contracts.json"
COUNTS = {"title_alias": 8, "semantic": 8, "scope_reference": 8, "constraint": 6,
          "ambiguity_absence": 4, "independence_session": 3, "failure_grounding": 3}


def artifacts():
    cases = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(cases) == 40 and len({case["id"] for case in cases}) == 40
    assert dict(Counter(c["category"] for c in cases)) == COUNTS
    assert Counter(c["split"] for c in cases) == {"development": 10, "held_out": 30}
    assert {c["source"] for c in cases} == {"real_catalog", "synthetic"}
    inventory = json.loads((ROOT / "docs/reports/conversational-rag-r0-config.json").read_text(encoding="utf-8"))
    assert inventory["status"] == "ok"
    actual_ids = {game["app_id"] for game in inventory["inventory"]}
    kinds = set(TurnPlan.model_fields["kind"].annotation.__args__)
    for case in cases:
        assert case["turns"]
        for turn in case["turns"]:
            assert 0 < len(turn["user"].strip()) <= 2000 and turn["expect"]
            expected = turn["expect"]
            if "kind" in expected:
                assert expected["kind"] in kinds
            for field in ("target_ids", "anchor_ids", "eligible_anchor_ids", "boundary_eligible_ids",
                          "forbidden_target_ids", "forbidden_card_ids", "clarification_ids"):
                assert not set(expected.get(field, [])) - actual_ids, (case["id"], field)
    schemas = {name: model.model_json_schema() for name, model in
               (("TurnPlan", TurnPlan), ("ChatStateV2", ChatStateV2), ("RetrievalOutcome", RetrievalOutcome))}
    schema_bytes = (json.dumps(schemas, indent=2, sort_keys=True) + "\n").encode()
    manifest = {
        "schema_version": 1, "frozen_at_phase": "R0", "catalog_version": inventory["catalog"]["version"],
        "dataset_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "contract_schemas_sha256": hashlib.sha256(schema_bytes).hexdigest(),
        "contract_prototype_sha256": hashlib.sha256(Path(__file__).with_name("contracts.py").read_bytes()).hexdigest(),
        "case_count": 40, "turn_count": sum(len(c["turns"]) for c in cases), "category_counts": COUNTS,
        "split_counts": {"development": 10, "held_out": 30},
        "development_ids": [c["id"] for c in cases if c["split"] == "development"],
        "source_counts": dict(Counter(c["source"] for c in cases)),
        "judgment_status": "Not executed or judged; semantic anchor IDs are curation seeds, not exhaustive relevance labels.",
        "baseline": "semantic-only cosine top-five, same catalog/encoder/generator/evidence budget/model settings",
        "rubric": {"0": "irrelevant or incorrect", "1": "partially useful with material missing fit or scope",
                   "2": "useful, relevant and correctly scoped"},
        "manual_review": ["all factual prose", "unsupported and false-absence claims", "subjective-fit qualifications",
                          "expected scope", "per-candidate relevance labels for Recall@8"],
        "execution_rules": ["Synthetic injection/browser cases are mandatory regressions, not real-catalog generation scores.",
            "Freeze any development-tuned cutoff/ranking policy before running held-out cases.",
            "No actual quality result or Recall@8 exists until complete judgments and per-method outputs are recorded.",
            "Live runs need separate approval, actual-turn/call/token budget, throttled sequential checkpoints.",
            "Input fixtures/contract changes require a new recorded manifest revision; never silently tune held-out expectations."],
    }
    return schema_bytes, (json.dumps(manifest, indent=2) + "\n").encode()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    schema, manifest = artifacts()
    if args.freeze:
        SCHEMAS.write_bytes(schema)
        MANIFEST.write_bytes(manifest)
    else:
        assert SCHEMAS.read_bytes() == schema, "Frozen schemas changed"
        assert MANIFEST.read_bytes() == manifest, "Frozen fixture/contract manifest changed"
    print(json.dumps({"status": "ok", "cases": 40, "split": "10 development / 30 held-out",
                      "mode": "freeze" if args.freeze else "check", "evaluation_executed": False}))
