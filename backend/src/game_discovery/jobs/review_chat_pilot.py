"""Replay recorded R4 JSON locally for diagnosis. ZERO inference/reservations.

Do not change prompts before the initial replay if byte-parity is required.
Output is a separate diagnostic artifact, never an overwritten pilot result.
"""

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from game_discovery.ai.chat_contracts import ChatStateV2, ChatTurn
from game_discovery.ai.chat_evidence import input_bytes
from game_discovery.ai.provider import AIFailure
from game_discovery.catalog.contracts import ConversationMessage
from game_discovery.catalog.repository import CatalogRepository
from game_discovery.core.settings import Settings
from game_discovery.db.engine import create_runtime_engine
from game_discovery.jobs.chat_evaluation import ROOT, RecordedRAG, SemanticBaseline, sha256
from game_discovery.jobs.evaluate_chat import PILOT_PATH, save
from game_discovery.retrieval.query import load_query_encoder


class ReplayModel:
    def __init__(self, attempts):
        self.attempts = iter(attempts)
        self.byte_parity = []

    def complete(self, instruction, data):
        attempt = next(self.attempts)
        self.byte_parity.append(input_bytes(instruction, data) == attempt["input_json_bytes"])
        if "output" not in attempt:
            raise AIFailure(attempt.get("error_code", "recorded_indeterminate_attempt"))
        return attempt["output"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=PILOT_PATH)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/reports/conversational-rag-r4-pilot-diagnosis.json")
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Use a new output in an existing directory")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    settings = Settings.from_environment()
    encoder = load_query_encoder(settings.query_tokenizer_path, settings.query_model_path, settings.query_artifact_path)
    if encoder is None or encoder.catalog_version != source["catalog_version"]:
        raise ValueError("matching_encoder_required")
    engine = create_runtime_engine(settings.database_url)
    report = {"pilot_sha256": sha256(args.source), "provider_calls": 0, "quota_reservations": 0, "records": []}
    try:
        repository = CatalogRepository(engine)
        for method in source["methods"]:
            state, messages, previous_case = ChatStateV2(), [], None
            for record in [r for r in source["records"] if r["method"] == method]:
                if record["case_id"] != previous_case:
                    state, messages = ChatStateV2(), []
                    previous_case = record["case_id"]
                attempts = [a for a in source["provider_attempts"] if a["method"] == method and a["turn"] == record["turn"]
                            and a["case_id"] == record["case_id"]
                            and a.get("revision") != "initial"]
                model = ReplayModel(attempts)
                rag = (RecordedRAG if method == "proposed" else SemanticBaseline)(model, repository, encoder)
                error_code = None
                validation_errors = []
                try:
                    result = rag.invoke(ChatTurn(message=record["user"], state=state, messages=messages))
                    state = result.state
                    messages += [ConversationMessage(role="user", content=record["user"]),
                                 ConversationMessage(role="assistant", content=result.message)]
                    messages = messages[-20:]
                    while sum(len(m.content) for m in messages) > 12000:
                        messages.pop(0)
                except AIFailure as error:
                    error_code = str(error)
                except ValidationError as error:
                    error_code = "invalid_provider_shape"
                    validation_errors = [{"location": list(e["loc"]), "type": e["type"]} for e in error.errors()]
                frame = rag.last_frame
                item = {"case_id": record["case_id"], "method": method, "turn": record["turn"], "error_code": error_code, "validation_errors": validation_errors,
                        "input_byte_parity": model.byte_parity}
                if frame and frame.packet:
                    raw_answer = next((a["output"] for a in attempts if a["stage"] == "generate"), {})
                    selected_ids = raw_answer.get("game_ids", [])
                    packet_ids = [d.metadata["app_id"] for d in frame.packet.documents]
                    item.update(evidence_ids=packet_ids, selected_ids=selected_ids,
                        unsupplied_selection_ids=sorted(set(selected_ids) - set(packet_ids)),
                        claims_for_unselected_ids=[c for c in raw_answer.get("claims", {}).get("claims", [])
                                                  if c["app_id"] not in selected_ids],
                        claims_outside_supplied_claimable_evidence=[c for c in raw_answer.get("claims", {}).get("claims", [])
                            if (c["app_id"], c["evidence_id"], c["field"]) not in frame.packet.claimable],
                        claimable_evidence=sorted([list(c) for c in frame.packet.claimable]))
                report["records"].append(item)
        save(args.output, report)
        print(json.dumps({"status": "ok", "byte_parity": all(v for r in report["records"] for v in r["input_byte_parity"]),
                          "provider_calls": 0, "quota_reservations": 0}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
