"""The normal Python build also provisions the pinned semantic runtime assets."""

import runpy
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).parent


class SemanticBuild(build_py):
    def run(self):
        runpy.run_path(str(ROOT / 'build_semantic.py'))['prepare'](ROOT / 'src/game_discovery/assets')
        super().run()


setup(cmdclass={'build_py': SemanticBuild})
