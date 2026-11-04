"""Compatibility command for the current scripted-provider assistant probe.

The October22 report remains historical. R2 changed the interpreter protocol, so
the current command writes R2 evidence instead of overwriting that earlier report.
"""

from pathlib import Path

from game_discovery.jobs.verify_chat_rag import main as verify_rag


def main() -> None:
    verify_rag(default_output=Path("docs/reports/conversational-rag-r2-integration.json"))


if __name__ == "__main__":
    main()
