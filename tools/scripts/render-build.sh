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

DRAFTS=
if [ "${IS_PULL_REQUEST:-}" = "true" ]; then
  DRAFTS=-D
fi

BASE=${RENDER_EXTERNAL_URL:-http://localhost:1315}
case $BASE in
  */) ;;
  *) BASE="${BASE}/" ;;
esac

"$HUGO_BIN" \
  --source "$ROOT" \
  --config "$ROOT/tools/hugo.yaml" \
  --minify --gc --cleanDestinationDir \
  --baseURL "$BASE" \
  $DRAFTS
