#!/bin/sh
# Build the HTML site for Render.
#
# Static Site settings:
#   Root directory:    empty
#   Build command:     sh tools/scripts/render-build.sh
#   Publish directory: tools/public
#
# Pull request previews are enabled on the service, Previews tab, Automatic.
# Render sets RENDER_EXTERNAL_URL and IS_PULL_REQUEST. A pull request build
# includes drafts, matching `make -C tools serve`. The main branch does not.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
HUGO_VERSION=0.168.0
HUGO_BIN=/tmp/hugo

if ! "$HUGO_BIN" version 2>/dev/null | grep -q "v${HUGO_VERSION}"; then
  curl -fsSL -o /tmp/hugo.tar.gz \
    "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_${HUGO_VERSION}_linux-amd64.tar.gz"
  tar -xzf /tmp/hugo.tar.gz -C /tmp hugo
fi

BASE=${RENDER_EXTERNAL_URL:-http://localhost:1315}
case $BASE in
  */) ;;
  *) BASE="${BASE}/" ;;
esac

# The posts a pull request adds or changes, as page paths for the header link.
# Read from GitHub rather than the local clone, which may be shallow and, for a
# fork, has no main branch. Any failure leaves the list empty.
changed_posts() {
  pr=$(printf '%s' "$BASE" | sed -n 's/.*-pr-\([0-9][0-9]*\)\..*/\1/p')
  [ -n "$pr" ] || return 0
  repo=https://github.com/dbazhenov/percona-test-blog-repo.git
  unshallow=
  if [ "$(git -C "$ROOT" rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]; then
    unshallow=--unshallow
  fi
  git -C "$ROOT" fetch --quiet --no-tags $unshallow "$repo" \
    "+refs/heads/main:refs/preview/main" "+refs/pull/$pr/head:refs/preview/head" 2>/dev/null || return 0
  fork_point=$(git -C "$ROOT" merge-base refs/preview/main refs/preview/head 2>/dev/null) || return 0
  git -C "$ROOT" diff --name-only --diff-filter=AMR "$fork_point" refs/preview/head -- posts 2>/dev/null \
    | sed -n -e 's#^posts/\([0-9]\{4\}\)/\([^/]*\)/.*#/blog/\1/\2#p' -e 's#^posts/\([0-9]\{4\}\)/\([^/]*\)\.md$#/blog/\1/\2#p' \
    | sort -u | tr '\n' ' '
}

DRAFTS=
if [ "${IS_PULL_REQUEST:-}" = "true" ]; then
  DRAFTS=-D
  HUGO_PARAMS_PREVIEWPOSTS=$(changed_posts || true)
  export HUGO_PARAMS_PREVIEWPOSTS
  echo "Posts in this pull request: ${HUGO_PARAMS_PREVIEWPOSTS:-none found}"
fi

"$HUGO_BIN" \
  --source "$ROOT" \
  --config "$ROOT/tools/hugo.yaml" \
  --minify --gc --cleanDestinationDir \
  --baseURL "$BASE" \
  $DRAFTS
