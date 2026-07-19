"""Build a DaDb stroke-order archive from KanjiVG.

Downloads the latest ``kanjivg-<date>-all.zip`` from ``KanjiVG/kanjivg`` and
repackages its SVGs, together with a DaDb ``index.json``, into
``out/kanjivg-dadb.zip`` — the archive DaKanji's ``kanjiVg`` importer reads.

Run locally with ``uv run main.py``; CI runs the same on a schedule and
publishes ``out/kanjivg-dadb.zip`` as ``releases/latest``.
"""

from __future__ import annotations

import io
import json
import urllib.request
import zipfile
from pathlib import Path

GITHUB_USER = "dariyooo"
GITHUB_REPO = "KanjiVG-DaDb"
UPSTREAM = "KanjiVG/kanjivg"

OUT_DIR = Path("out")
ARCHIVE_NAME = "kanjivg-dadb.zip"

_BASE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest/download"


def _latest_release() -> dict:
    url = f"https://api.github.com/repos/{UPSTREAM}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "KanjiVG-DaDb"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def _asset_url(release: dict, ends_with: str) -> str:
    for asset in release["assets"]:
        if asset["name"].endswith(ends_with):
            return asset["browser_download_url"]
    raise SystemExit(f"asset *{ends_with} not found in {UPSTREAM} latest release")


def _index_json(revision: str) -> bytes:
    return json.dumps(
        {
            "title": "KanjiVG",
            "revision": revision,
            "isUpdatable": True,
            "indexUrl": f"{_BASE}/index.json",
            "downloadUrl": f"{_BASE}/{ARCHIVE_NAME}",
            "url": f"https://github.com/{UPSTREAM}",
            "author": "Ulrich Apel / KanjiVG",
            "attribution": "KanjiVG © Ulrich Apel, CC BY-SA 3.0",
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def main() -> None:
    release = _latest_release()
    revision = release["tag_name"]

    req = urllib.request.Request(
        _asset_url(release, "-all.zip"), headers={"User-Agent": "KanjiVG-DaDb"}
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()

    OUT_DIR.mkdir(exist_ok=True)
    index = _index_json(revision)
    (OUT_DIR / "index.json").write_bytes(index)
    with zipfile.ZipFile(io.BytesIO(raw)) as upstream, zipfile.ZipFile(
        OUT_DIR / ARCHIVE_NAME, "w", zipfile.ZIP_DEFLATED
    ) as out:
        out.writestr("index.json", index)
        for name in upstream.namelist():
            if name.endswith(".svg"):
                out.writestr(Path(name).name, upstream.read(name))

    print(f"wrote {OUT_DIR / ARCHIVE_NAME} (revision {revision})")


if __name__ == "__main__":
    main()
