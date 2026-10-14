import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from game_discovery.jobs.environment_check import db_url_matches_project, normalize_db_url, read_only_db_check, role_identity, run_environment_check


class EnvironmentCheckTests(unittest.TestCase):
    def test_pooler_tenant_suffix_is_not_a_distinct_role(self):
        project_url = "https://exampleproject.supabase.co"
        direct = "postgresql://postgres:secret@db.exampleproject.supabase.co/postgres"
        pooler = "postgresql://postgres.exampleproject:secret@aws-0-eu.pooler.supabase.com/postgres"
        self.assertEqual(role_identity(direct, project_url), role_identity(pooler, project_url))

    def test_authentication_error_exposes_only_allowlisted_failure_code(self):
        secret = "never-display-this-password"
        with patch("psycopg.connect", side_effect=RuntimeError(f"password authentication failed: {secret}")), \
                patch("socket.getaddrinfo", return_value=[]):
            report = read_only_db_check(f"postgresql://user:{secret}@db.exampleproject.supabase.co/postgres")
        self.assertEqual(report["failure_code"], "authentication_failed")
        self.assertNotIn(secret, json.dumps(report))

    def test_wrong_project_is_not_contacted_and_output_does_not_leak_secrets(self):
        project_url = "https://exampleproject.supabase.co"
        secret = "never-display-this-password"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                f'DATABASE_URL="postgresql://postgres:{secret}@db.otherproject.supabase.co:5432/postgres"\n'
                f'GROQ_API_KEY="{secret}"\n', encoding="utf-8"
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_environment_check(path, project_url, connect=True)
            self.assertEqual(exit_code, 1)
            self.assertNotIn(secret, stdout.getvalue())
            self.assertNotIn("otherproject", stdout.getvalue())
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["connections"]["DATABASE_URL"]["status"], "skipped")

    def test_direct_and_pooler_identity(self):
        project_url = "https://exampleproject.supabase.co"
        self.assertTrue(db_url_matches_project("postgresql://user:secret@db.exampleproject.supabase.co/postgres", project_url))
        self.assertTrue(db_url_matches_project("postgresql+psycopg://runtime.exampleproject:secret@aws-0-eu.pooler.supabase.com/postgres", project_url))
        self.assertFalse(db_url_matches_project("postgresql://runtime.other:secret@aws-0-eu.pooler.supabase.com/postgres", project_url))
        raw_url = "postgresql://runtime:password@extra@db.exampleproject.supabase.co/postgres"
        self.assertTrue(db_url_matches_project(raw_url, project_url))
        self.assertEqual(normalize_db_url(raw_url), "postgresql://runtime:password%40extra@db.exampleproject.supabase.co/postgres")
        self.assertEqual(normalize_db_url(normalize_db_url(raw_url)), normalize_db_url(raw_url))
        self.assertFalse(db_url_matches_project("postgresql://runtime:secret@db.exampleproject.supabase.co:INVALID/postgres", project_url))
