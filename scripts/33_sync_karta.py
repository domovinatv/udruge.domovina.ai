"""Preslikaj udruge.geojson u ../karta-hrvatske (gis.domovina.ai).

Sloj na zajedničkoj karti živi u OVOM repou (export), a karta ga samo
preslika — `karta-web/public/data/` je gitignored pa sloj nestane na svježem
checkoutu ako se ne pokrene ovaj korak (ili `npm run sync-data` ondje).

  uv run python scripts/33_sync_karta.py
"""
from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sync-karta")

SRC = ROOT / "data" / "exports" / "udruge.geojson"
DEFAULT_KARTA = ROOT.parent / "karta-hrvatske" / "apps" / "karta-web" / "public" / "data"


def run() -> None:
    dst_dir = Path(os.environ.get("KARTA_DATA_DIR", str(DEFAULT_KARTA)))
    if not dst_dir.parent.exists():
        log.warning("nema ../karta-hrvatske (%s) — preskačem", dst_dir)
        return
    if not SRC.exists():
        raise SystemExit(f"{SRC} ne postoji — pokreni `make export`.")
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, dst_dir / SRC.name)
    log.info("%s → %s (%.0f KB)", SRC.name, dst_dir, SRC.stat().st_size / 1024)


if __name__ == "__main__":
    sys.exit(run())
