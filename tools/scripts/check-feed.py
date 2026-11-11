#!/usr/bin/env python3
"""Validate public/wordpress.json against the feed contract."""

import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent


def fail(message: str) -> None:
    print(f"FAIL {message}", file=sys.stderr)
    sys.exit(1)


def categories() -> set[str]:
    names = set()
    for line in (APP / "data" / "wp-categories.txt").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line)
    return names


def local_image(url: str, asset_base: str) -> Path | None:
    """Path under public/ for an image this site publishes. External URLs are skipped."""
    path = url
    if url.startswith(("http://", "https://")):
        base = asset_base.rstrip("/")
        if not (base and (url == base or url.startswith(base + "/"))):
            return None
        path = url[len(base):] or "/"
    elif url.startswith("//"):
        return None
    if not path.startswith("/"):
        return None
    rel = Path(path.lstrip("/"))
    if ".." in rel.parts:
        fail(f"image path escapes the site: {url}")
    return APP / "public" / rel


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else APP / "public" / "wordpress.json")
    raw = path.read_text()
    if not raw.lstrip().startswith("{"):
        fail("feed does not start with a JSON object")
    if "SECRET DRAFT BODY" in raw or "Draft not in feed" in raw:
        fail("draft title or body leaked into the feed")

    data = json.loads(raw)
    if data.get("version") != 1:
        fail("version must be 1")
    if not isinstance(data.get("posts"), list):
        fail("posts must be a list")
    if len(data["posts"]) > 500:
        fail("feed has more than 500 posts")
    asset_base = data.get("asset_base", "")
    if not isinstance(asset_base, str):
        fail("asset_base must be a string")
    if asset_base.startswith("http://"):
        fail("asset_base in the public feed must not be http")

    allowed = categories()
    seen_ids = set()
    seen_slugs = set()
    publish_keys = {
        "id",
        "status",
        "slug",
        "title",
        "date",
        "excerpt",
        "html",
        "tags",
        "categories",
        "authors",
        "origin",
        "image",
        "path",
        "expected_url",
    }

    for post in data["posts"]:
        status = post.get("status")
        post_id = post.get("id")
        if not isinstance(post_id, str) or not post_id:
            fail("post is missing id")
        if post_id in seen_ids:
            fail(f"duplicate id {post_id}")
        seen_ids.add(post_id)

        if status == "draft":
            extra = set(post) - {"id", "status"}
            if extra:
                fail(f"draft stub {post_id} leaks {sorted(extra)}")
            continue
        if status != "publish":
            fail(f"{post_id} has status {status}")
        missing = publish_keys - set(post)
        if missing:
            fail(f"{post_id} is missing {sorted(missing)}")
        if post["slug"] in seen_slugs:
            fail(f"duplicate slug {post['slug']}")
        seen_slugs.add(post["slug"])
        if post.get("origin") not in {"percona", "community"}:
            fail(f"{post_id} origin must be percona or community")
        if not post["html"].strip():
            fail(f"{post_id} has empty html")
        for category in post["categories"]:
            if category not in allowed:
                fail(f"{post_id} uses unknown category {category!r}. Use a name from tools/data/wp-categories.txt, or open an issue to add one.")
        for author in post["authors"]:
            slug = author.get("slug", "")
            page = ROOT / "authors" / slug / "index.md"
            if not page.is_file():
                fail(f"{post_id} references unknown author {slug}")
            if author.get("id") != slug:
                fail(f"{post_id} author id {author.get('id')!r} does not match {slug}")
            if not __import__("re").fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                fail(f"{post_id} author {slug} must be name-surname: lowercase letters, digits, and hyphens. Not name_surname or name.surname.")
            if author.get("type") not in {"staff", "community"}:
                fail(f"{post_id} author {slug} type must be staff or community")
            if post.get("origin") == "percona" and author.get("type") != "staff":
                fail(f"{post_id} is a Percona post but {slug} is not staff")
            if not author.get("name"):
                fail(f"{post_id} author {slug} has no name")
            portrait = author.get("image") or ""
            if portrait:
                image = local_image(portrait, asset_base)
                if image is not None and not image.is_file():
                    fail(f"{post_id} author {slug} references missing image {portrait}")
        for url in [post["image"], *img_srcs(post["html"])]:
            if not url:
                continue
            image = local_image(url, asset_base)
            if image is not None and not image.is_file():
                fail(f"{post_id} references missing image {url}")

    check_samples(data)
    print(f"feed ok ({len(data['posts'])} posts)")


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


def check_samples(data: dict) -> None:
    posts = {post["id"]: post for post in data["posts"]}
    hello = posts.get("2026-11-10-hello-percona-blog")
    if hello:
        names = [author["name"] for author in hello["authors"]]
        if names != ["Alex Example"]:
            fail(f"hello authors are {names}")
        if hello["slug"] != "hello-percona-blog":
            fail(f"hello slug is {hello['slug']}")
        if not hello["expected_url"].endswith("/hello-percona-blog/"):
            fail(f"hello url is {hello['expected_url']}")
        needle = "/2026-11-10-hello-percona-blog/hello-percona-blog.png"
        if needle not in hello["image"] or needle not in hello["html"]:
            fail(f"hello image is {hello['image']}")
    mysql = posts.get("2026-11-10-mysql-connection-pool")
    if mysql:
        if "language-sql" not in mysql["html"]:
            fail("mysql sample lost its code fence")
        if [author["name"] for author in mysql["authors"]] != ["Alex Example", "Sam Sample"]:
            fail("mysql sample authors were not resolved")
        if mysql["categories"] != ["MySQL"]:
            fail("mysql sample category changed")
    draft = posts.get("2026-11-11-draft-not-in-feed")
    if draft and draft.get("status") != "draft":
        fail("sample draft is not a stub")


if __name__ == "__main__":
    main()
