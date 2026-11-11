# Agent notes for this blog

The author already has a finished post, in a Google Doc, a docx file, a PDF, or Markdown. Prepare that post for this repository as Markdown and open a pull request. Do not write a new article. Do not edit `tools/` unless asked. Do not mention the publishing system in commit messages or in text you add to a post.

After cloning, from the repository root:

```bash
make -C tools serve    # http://localhost:1314/ , drafts included
make -C tools check    # run this before a pull request
```

`make -C tools check` must pass. It fails on a missing author page, a bad author id, a category that is not listed, or an image that is not next to the post.

## Author

Path: `authors/<id>/index.md`. Look at the other authors in `authors/`.

`id` and the folder name are the same string: `name-surname`. Lowercase letters, digits, hyphens. Example: `pablo-svampa`. Reject `name_surname`, `name.surname`, and capitals. `name` is the display name. `type` is `staff` or `community`. Portrait file sits in that folder; `image` is its filename. Text under the front matter is the bio.

## Post

Path: `posts/<year>/slug/index.md`. Copy `tools/archetypes/blog.md`. A post with no images may be `posts/<year>/slug.md` instead. Do not put a date in the filename. The publication date is written when the post is published.

- `id`: set once to the original filename without `.md`. Never change it. Renaming the file is safe only while `id` stays.
- Public address: the filename. `mysql-connection-pool` is published at `/blog/mysql-connection-pool/`. Set `slug` only to override that.
- `authors`: author ids, not display names.
- `origin`: `percona` or `community`. A `percona` post lists only `staff` authors.
- `categories`: exact names from `tools/data/wp-categories.txt`. Do not invent one. Ask with an issue.
- `images`: the first file is the cover. Every post needs a cover at 1200×630, the Open Graph size. If the author knows how it should look, prepare that file. If they do not, leave the cover unset and say in the pull request that the team will make it. Other images sit next to `index.md` and are referenced by filename, `![alt](diagram.png)`. Do not resize them in the build. About 1600px wide is enough for the 855px article column. Use JPEG or WebP for photos, PNG or WebP for screenshots and diagrams. Keep each file around 200–400 KB. A file of 3–4 MB is too heavy. `make -C tools check` does not measure file size. An author portrait is square, about 400px. For a diagram, use a `mermaid` code fence instead of a screenshot. The preview draws it.
- `draft: true` hides the post from the published site and leaves it unpublished. The pull request preview and `make -C tools serve` still show it. Deleting the file does not unpublish. To unpublish, keep the file and set `draft: true`.
- `date`: the author value is for the preview only. The publish build replaces it when the post first goes out. Do not change `date` on a later edit.

## Pull request and edits

Open a pull request. `make -C tools check` must pass before asking for review. When the preview build finishes, a comment on the pull request links to the built site. The post is merged only after an approve from 3 experts. Do not merge with fewer approvals. The same rule applies to an edit of a published post. If the pull request gets no reviewers or is declined, close it. The post did not catch interest. Start a different one.

Edits: for about three days after publication, change the post in a new pull request. After about three days, do not expect a git edit to replace the published text. Open an issue that names the post and the change.
