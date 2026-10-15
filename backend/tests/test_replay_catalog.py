"""Offline checks only: these tests never connect to a database or execute Actions."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from game_discovery.jobs.catalog import load_games, normalize
from game_discovery.jobs.replay_catalog import REPOSITORY, materialize_fixture, replay_environment

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "data" / "fixtures" / "m2-replay-sources.json"
IDENTITIES = ROOT / "data" / "fixtures" / "m2-app-ids.json"


class ReplayCatalogTests(unittest.TestCase):
    def test_frozen_sources_normalize_reproducibly_with_original_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = materialize_fixture(FIXTURE, IDENTITIES, root / "first")
            second = materialize_fixture(FIXTURE, IDENTITIES, root / "second")
            self.assertEqual(first, second)
            self.assertEqual(normalize(root / "first"), normalize(root / "second"))
            games, manifest = load_games(root / "first")
            self.assertEqual(manifest["games"], 40)
            self.assertTrue(any(game.app_id == 1145360 for game in games))
            self.assertTrue(any(game.free_to_play is True for game in games))
            self.assertTrue(any(game.early_access is True for game in games))
            self.assertFalse(manifest["quarantine"])
            observation = json.loads((root / "first" / "collection.json").read_text(encoding="utf-8"))["observations"][0]
            self.assertEqual(observation["snapshot_kind"], "frozen-field-projection")
            self.assertNotEqual(observation["original_http_sha256"], observation["source"]["sha256"])
            self.assertEqual(observation["source"]["collected_at"][:10], "2026-10-14")

    def test_fixture_rejects_duplicate_ids_and_unrelated_source_urls(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            for defect in ("duplicate", "url"):
                packed = json.loads(FIXTURE.read_text(encoding="utf-8"))
                if defect == "duplicate":
                    packed["records"][0] = packed["records"][1]
                else:
                    packed["records"][0]["original_source"]["url"] = "https://unrelated.example/"
                path.write_text(json.dumps(packed), encoding="utf-8")
                with self.assertRaises(ValueError):
                    materialize_fixture(path, IDENTITIES, Path(temporary) / defect)

    def test_replay_refuses_local_or_unrelated_context_before_database_access(self):
        from game_discovery.jobs.replay_catalog import main
        with patch.dict("os.environ", {}, clear=True), patch("psycopg.connect") as connect:
            with self.assertRaises(ValueError):
                main()
            connect.assert_not_called()

    def test_replay_guard_accepts_only_dedicated_temp_root_and_ephemeral_port(self):
        with tempfile.TemporaryDirectory() as temporary:
            env = {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": REPOSITORY, "RUNNER_ENVIRONMENT": "github-hosted",
                   "RUNNER_TEMP": temporary, "M2_REPLAY_ROOT": str(Path(temporary) / "m2-clean-replay"), "M2_REPLAY_PORT": "25432"}
            self.assertEqual(replay_environment(env), ((Path(temporary) / "m2-clean-replay").resolve(), 25432))
            for patch_values in ({"M2_REPLAY_ROOT": temporary}, {"M2_REPLAY_PORT": "443"},
                                 {"GITHUB_REPOSITORY": "another/repository"}, {"RUNNER_ENVIRONMENT": "self-hosted"}):
                with self.assertRaises(ValueError):
                    replay_environment({**env, **patch_values})

    def test_workflow_is_manual_only_without_secrets_or_deployment_access(self):
        text = (ROOT / ".github" / "workflows" / "m2-clean-replay.yml").read_text(encoding="utf-8")
        workflow = yaml.safe_load(text)
        self.assertEqual(workflow["on"], {"workflow_dispatch": None})
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertNotRegex(text, r"\$\{\{\s*secrets[.\[]")
        job = workflow["jobs"]["replay"]
        self.assertEqual(job["runs-on"], "ubuntu-24.04")
        self.assertLessEqual(job["timeout-minutes"], 20)
        service = job["services"]["postgres"]
        self.assertIn("pgvector/pgvector@sha256:", service["image"])
        self.assertNotIn("volumes", service)
        self.assertEqual(service["ports"], ["5432/tcp"])
        self.assertEqual(job["env"]["DATABASE_URL"], "")
        self.assertEqual(job["env"]["MIGRATION_DATABASE_URL"], "")
        self.assertEqual(job["steps"][-1]["if"], "always()")
        self.assertIn("rm -rf", job["steps"][-1]["run"])
