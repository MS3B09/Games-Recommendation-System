import unittest
from types import SimpleNamespace

from game_discovery.jobs.api_benchmark import process_tree_memory


class ProcessTreeMemoryTests(unittest.TestCase):
    def test_launcher_rss_alone_does_not_hide_model_process_memory(self):
        model = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=250_000_000))
        launcher = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=3_000_000),
                                   children=lambda recursive: [model])
        resident, processes = process_tree_memory(launcher)
        self.assertEqual(resident, 253_000_000)
        self.assertEqual(len(processes), 2)
