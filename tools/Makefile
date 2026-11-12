.PHONY: build check package serve preview

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
HUGO ?= hugo
HUGO_CACHE := $(ROOT)/tools/.hugo-cache
HUGO_FLAGS := --source $(ROOT) --config $(ROOT)/tools/hugo.yaml

build:
	$(HUGO) $(HUGO_FLAGS) -D --minify --gc --cleanDestinationDir --cacheDir $(HUGO_CACHE)

check: build
	python3 $(ROOT)/tools/scripts/check-feed.py $(ROOT)/tools/public/wordpress.json

package: build
	python3 $(ROOT)/tools/scripts/package-feed.py

serve:
	$(HUGO) $(HUGO_FLAGS) server -D --disableFastRender --renderToMemory --bind 127.0.0.1 --port 1314 --baseURL http://localhost:1314/ --appendPort=false --cacheDir $(HUGO_CACHE)

# HTML for posts that are not drafts.
preview:
	$(HUGO) $(HUGO_FLAGS) --minify --gc --cleanDestinationDir --baseURL http://localhost:1315/ --cacheDir $(HUGO_CACHE)
	@echo "Preview files are in tools/public/. Draft posts are not included."
