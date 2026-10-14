import argparse
import json
import sys
from pathlib import Path

from game_discovery.jobs.audit import run_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproducible game discovery developer jobs")
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Stream CSV coverage and identity audit")
    audit.add_argument("--input", type=Path, action="append", required=True)
    audit.add_argument("--output", type=Path, required=True)
    probe = commands.add_parser("probe", help="Small sequential Steam source feasibility probe")
    probe.add_argument("--app-id", type=int, action="append", required=True)
    probe.add_argument("--output-dir", type=Path, required=True)
    probe.add_argument("--reviews", action="store_true", help="Probe aggregate reviews without requesting review text")
    benchmark = commands.add_parser("encoder-benchmark", help="CPU ONNX memory, latency and representation comparison")
    benchmark.add_argument("--cache-dir", type=Path, required=True)
    benchmark.add_argument("--output", type=Path, required=True)
    for name, description in (("encoder-parity", "CPU offline/ONNX representation and long-input parity"),
                              ("offline-reference", "CPU reference process used by encoder-parity")):
        parity = commands.add_parser(name, help=description)
        parity.add_argument("--cache-dir", type=Path, required=True)
        parity.add_argument("--output", type=Path, required=True)
    environment = commands.add_parser("environment-check", help="Redacted configuration and optional read-only DB check")
    environment.add_argument("--env-file", type=Path, required=True)
    environment.add_argument("--project-url", required=True, help="Public Supabase URL from the connected MCP project")
    environment.add_argument("--connect", action="store_true", help="Verify configured DB URLs using read-only queries")
    sizing = commands.add_parser("database-sizing", help="Import isolated quarantined sizing fixtures and measure storage")
    sizing.add_argument("--input", type=Path, required=True)
    sizing.add_argument("--limit", type=int, default=3000)
    sizing.add_argument("--env-file", type=Path, required=True)
    sizing.add_argument("--project-url", required=True)
    sizing.add_argument("--output", type=Path, required=True)
    api = commands.add_parser("api-benchmark", help="Loopback HTTP process memory/latency feasibility")
    api.add_argument("--cache-dir", type=Path, required=True)
    api.add_argument("--env-file", type=Path, required=True)
    api.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "audit":
            report = run_audit(args.input, args.output)
            print(json.dumps({"job": "audit", "status": "ok", "report": str(args.output),
                              "rows": [item["rows"] for item in report["datasets"]]}))
            return 0
        if args.command == "probe":
            from game_discovery.jobs.probe import run_probe
            return run_probe(args.app_id, args.output_dir, args.reviews)
        if args.command == "encoder-benchmark":
            from game_discovery.jobs.encoder_benchmark import run_benchmark
            return run_benchmark(args.cache_dir, args.output)
        if args.command == "database-sizing":
            from game_discovery.jobs.database_sizing import run_sizing
            return run_sizing(args.input, args.limit, args.env_file, args.project_url, args.output)
        if args.command in {"encoder-parity", "offline-reference"}:
            from game_discovery.jobs.encoder_parity import run_parity, run_reference
            runner = run_parity if args.command == "encoder-parity" else run_reference
            return runner(args.cache_dir, args.output)
        if args.command == "api-benchmark":
            from game_discovery.jobs.api_benchmark import run_api_benchmark
            return run_api_benchmark(args.cache_dir, args.env_file, args.output)
        from game_discovery.jobs.environment_check import run_environment_check
        return run_environment_check(args.env_file, args.project_url, args.connect)
    except (OSError, ValueError) as error:
        print(json.dumps({"job": args.command, "status": "failed", "error_type": type(error).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
