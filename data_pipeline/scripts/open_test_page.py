"""Open the local Day 2 test page in the default browser."""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.generate_status_snapshot import run as run_status_snapshot


def run() -> Path:
    html_path = Path("outputs/day2_test_page.html")
    if not html_path.exists():
        _, generated_html_path = run_status_snapshot()
        html_path = generated_html_path

    absolute_html = html_path.resolve()
    subprocess.run(["open", str(absolute_html)], check=False)
    print(f"Opened test page: {absolute_html}")
    return absolute_html


if __name__ == "__main__":
    run()