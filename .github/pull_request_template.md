## Post

- [ ] The file is `posts/<year>/slug.md`, or `.../slug/index.md` when the post has images. The filename has no date
- [ ] `authors/<id>/index.md` exists, and each author id is `name-surname`
- [ ] Categories match `tools/data/wp-categories.txt`
- [ ] The cover is 1200×630, or the pull request says the team should make it. Other images sit next to `index.md` and are referenced by filename (`diagram.png`). Each file is about 200–400 KB, not several MB
- [ ] `make -C tools serve` looks right, and `make -C tools check` passes
- [ ] `draft: true` is set only when this merge should stay unpublished
