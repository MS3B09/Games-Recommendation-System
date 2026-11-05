import hashlib
import json
import os
import runpy
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from game_discovery.core.settings import Settings

BUILD = Path(__file__).resolve().parents[1] / 'build_semantic.py'


class SemanticBuildTests(unittest.TestCase):
    def test_build_downloads_verified_files_reuses_cache_and_rejects_corruption(self):
        prepare = runpy.run_path(str(BUILD))['prepare']
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            artifact = {'model_id': 'sentence-transformers/all-MiniLM-L6-v2',
                        'model_revision': '1110a243fdf4706b3f48f1d95db1a4f5529b4d41', 'dimensions': 384,
                        'tokenizer_sha256': hashlib.sha256(b'tokenizer').hexdigest(),
                        'model_sha256': hashlib.sha256(b'model').hexdigest()}
            artifact['version'] = 'm2-' + hashlib.sha256(json.dumps(
                artifact, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:24]
            (directory / 'artifact.json').write_text(json.dumps(artifact), encoding='utf-8')
            with patch.dict(prepare.__globals__, urlopen=lambda *_args, **_kwargs: BytesIO(b'wrong')):
                with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                    prepare(directory)
            self.assertEqual(sorted(p.name for p in directory.iterdir()), ['artifact.json'])
            streams = iter([BytesIO(b'tokenizer'), BytesIO(b'model')])
            with patch.dict(prepare.__globals__, urlopen=lambda *_args, **_kwargs: next(streams)):
                prepare(directory)
                prepare(directory)  # Any additional network call exhausts the iterator.
            (directory / 'model.onnx').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'Cached semantic asset checksum mismatch'):
                prepare(directory)
            artifact['dimensions'] = 1
            (directory / 'artifact.json').write_text(json.dumps(artifact), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Invalid bundled catalog'):
                prepare(directory)

    def test_deployed_defaults_are_portable_and_explicit_paths_still_win(self):
        with patch.dict(os.environ, {'GAME_DISCOVERY_ENV_FILE': 'nonexistent'}, clear=True):
            settings = Settings.from_environment()
            self.assertEqual(Path(settings.query_model_path).name, 'model.onnx')
            self.assertEqual(Path(settings.query_artifact_path).name, 'artifact.json')
            self.assertEqual(Path(settings.query_artifact_path).parent.name, 'assets')
            with patch.dict(os.environ, QUERY_MODEL_PATH='explicit.onnx', QUERY_TOKENIZER_PATH=''):
                self.assertEqual(Settings.from_environment().query_model_path, 'explicit.onnx')
                self.assertEqual(Settings.from_environment().query_tokenizer_path, '')
