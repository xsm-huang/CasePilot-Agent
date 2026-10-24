"""Run the Python API and Vite directly; stop only the children we create."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    node = shutil.which("node")
    vite = ROOT / "apps/web/node_modules/vite/bin/vite.js"
    compiler = ROOT / "packages/contracts/node_modules/typescript/bin/tsc"
    if not node or not vite.is_file() or not compiler.is_file():
        print("Frontend dependencies missing. Run pnpm install first.", file=sys.stderr)
        return 1
    # Compile the shared contract before Vite resolves its package exports.
    result = subprocess.run(
        [node, str(compiler), "-p", "tsconfig.json"], cwd=ROOT / "packages/contracts", check=False
    )
    if result.returncode:
        return result.returncode
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {}
    children = []
    try:
        children.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "casepilot",
                ],
                cwd=ROOT,
                **options,
            )
        )
        children.append(subprocess.Popen([node, str(vite)], cwd=ROOT / "apps/web", **options))
        while all(child.poll() is None for child in children):
            time.sleep(0.2)
        return next((child.returncode or 1 for child in children if child.poll() is not None), 1)
    except KeyboardInterrupt:
        return 0
    finally:
        for child in reversed(children):
            if child.poll() is not None:
                continue
            if os.name == "nt":
                child.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
