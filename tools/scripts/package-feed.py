#!/usr/bin/env python3
"""Copy wordpress.json and the images it references into feed-out/.

Draft stubs have no image fields, so their files stay out of the package.
HTML is never copied.
"""

import json
import shutil
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PUBLIC = APP / "public"
OUT = APP / "feed-out"


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    sys.exit(1)


def img_srcs(html: str) -> list[str]:
    srcs = []
    needle = 'src="'
    start = 0
    while True:
        found = html.find(needle, start)
        if found < 0:
            return srcs
        value_start = found + len(needle)
        value_end = html.find('"', value_start)
        if value_end < 0:
            return srcs
        srcs.append(html[value_start:value_end])
        start = value_end + 1


def local_path(url: str, asset_base: str) -> Path | None:
    if not url:
        return None
    path = url
    if url.startswith(("http://", "https://")):
        base = asset_base.rstrip("/")
        if not (base and (url == base or url.startswith(base + "/"))):
            return None
        path = url[len(base):] or "/"
    elif url.startswith("//"):
        return None
    if not path.startswith("/"):
        path = "/" + path
    rel = Path(path.lstrip("/"))
    if ".." in rel.parts:
        fail(f"image path escapes the site: {url}")
    return PUBLIC / rel


def main() -> None:
    feed_path = PUBLIC / "wordpress.json"
    if not feed_path.is_file():
        fail("public/wordpress.json is missing")
    data = json.loads(feed_path.read_text())
    asset_base = data.get("asset_base") or ""
    if not isinstance(asset_base, str):
        fail("asset_base must be a string")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(feed_path, OUT / "wordpress.json")

    copied: set[Path] = set()
    for post in data.get("posts", []):
        if post.get("status") != "publish":
            continue
        urls = [post.get("image") or "", *img_srcs(post.get("html") or "")]
        for author in post.get("authors") or []:
            if isinstance(author, dict):
                urls.append(author.get("image") or "")
        for url in urls:
            src = local_path(url, asset_base)
            if src is None:
                continue
            if not src.is_file():
                fail(f"{post.get('id')} references missing image {url}")
            rel = src.relative_to(PUBLIC)
            if rel in copied:
                continue
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest)
            copied.add(rel)

    html = list(OUT.rglob("*.html"))
    if html:
        fail("feed-out contains HTML")
    print(f"packaged {len(copied)} images")


if __name__ == "__main__":
    main()
