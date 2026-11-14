"""
Run one ingestion from GitHub Actions and record it in ingestion_runs.

Run from the Backend folder:

    python -m scripts.ciIngest --market canada --trigger manual

The workflow in .github/workflows/ingest.yml calls this on its schedule
and when started by hand. A failure exits non-zero, so the run shows red.
"""

import argparse
import asyncio

from dotenv import load_dotenv

load_dotenv()

from app.ingestion.runner import run_ingestion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", default="canada")
    parser.add_argument("--trigger", default="scheduled", choices=["scheduled", "manual"])
    args = parser.parse_args()

    result = asyncio.run(run_ingestion(args.market, args.trigger))

    print(f"Finished: {result['inserted']} new jobs ({args.market}, {args.trigger}).")


if __name__ == "__main__":
    main()
