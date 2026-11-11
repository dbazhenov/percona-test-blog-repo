#!/bin/sh
# Publish tools/feed-out as the single commit on the feed branch.
# Authors do not commit there. The next build replaces the branch.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/tools/feed-out"
BRANCH="${FEED_BRANCH:-feed}"

if [ ! -f "$OUT/wordpress.json" ]; then
  echo "tools/feed-out/wordpress.json is missing. Run make -C tools package first." >&2
  exit 1
fi

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT
cp -R "$OUT"/. "$WORKDIR"/
cat > "$WORKDIR/README.md" << 'EOF'
# feed

The publish build on main replaces this branch. It contains the JSON feed and the original image files. Authors do not edit it. The next successful build overwrites it.
EOF

git -C "$WORKDIR" init -b "$BRANCH"
git -C "$WORKDIR" add -A
git -C "$WORKDIR" \
  -c user.name="github-actions[bot]" \
  -c user.email="41898282+github-actions[bot]@users.noreply.github.com" \
  commit -m "Publish the feed"

if [ -n "${FEED_REMOTE:-}" ]; then
  git -C "$WORKDIR" push --force "$FEED_REMOTE" "HEAD:refs/heads/$BRANCH"
  exit 0
fi

if [ -z "${GITHUB_TOKEN:-}" ] || [ -z "${GITHUB_REPOSITORY:-}" ]; then
  echo "Set FEED_REMOTE, or GITHUB_TOKEN and GITHUB_REPOSITORY." >&2
  exit 1
fi

git -C "$WORKDIR" \
  -c http.extraheader="AUTHORIZATION: bearer ${GITHUB_TOKEN}" \
  push --force "https://github.com/${GITHUB_REPOSITORY}.git" "HEAD:refs/heads/$BRANCH"
