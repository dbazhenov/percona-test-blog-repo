# Agent notes for this blog

This repository holds the posts of percona.com/blog. Your job is narrow: the author already has a finished post, in a Google Doc, a docx file, a PDF, or Markdown. Turn that post into a Markdown file here and open a pull request. Do not write a new article, and do not rewrite the author's text beyond fixing the formatting.

## What you may change

- `posts/<year>/<id>/`: the new post and its images.
- `authors/<author-id>/`: the author page, only if the author does not have one yet.

That is all. Do not change anything else:

- `tools/` is the build: templates, styles, scripts, the category list. Do not edit it, even if the preview looks wrong or the check fails. Report the problem to the author instead.
- `.github/` holds the workflows. Do not edit it.
- Other posts and other authors' pages are not part of the job.
- Do not commit to `main` or to the `feed` branch, and do not merge the pull request. A post is merged by people, after review.

Do not mention the publishing system in commit messages or in text you add to a post.

## Ask the author first

Look in `authors/` and in the draft first. Ask only what you cannot find there, rather than guess:

- Their author id, `name-surname`. Check `authors/` for an existing page.
- If there is no page: display name, role, company, a short bio, a square portrait, GitHub and LinkedIn if they want them.
- Whether they are a Percona employee (`origin: percona`, author `type: staff`) or a community author (`origin: community`, `type: community`).
- The category, if the post does not make it obvious.
- The cover image, 1200×630. If they have none, leave `images` without a cover and say in the pull request that the team will make it.

## Steps

1. Create a branch from `main` named `blog/<id>`, for example `blog/mysql-connection-pool`.
2. Pick a recent post in `posts/` with a similar shape and use it as the model for the text. Many older posts were imported from WordPress with a date in the folder name, a dated `id`, and a `slug`. Do not copy those: when a post and these notes disagree, follow these notes. Do not use `tools/archetypes/blog.md` either: it sets `draft: true`, and a draft is never published.
3. Create `posts/<year>/<id>/index.md`. Put images next to it. A post with no images may be a single file, `posts/<year>/<id>.md`.
4. Fill the front matter (below), then the text. Keep the author's words, headings, and order.
5. Create the author page if needed.
6. Run the check (below). It must pass.
7. Commit and open a pull request against `main`. Fill in the pull request template: who the post is for, and anything missing, such as the cover. A community author without write access opens it from a fork.

## Front matter

```yaml
title: "Why the replica fell behind"
id: why-the-replica-fell-behind
date: "2026-11-12T09:00:00-08:00"
draft: false
origin: percona
description: "One or two sentences. This is the summary on the blog."
authors:
  - name-surname
categories:
  - MySQL
tags:
  - replication
images:
  - cover.png
```

- `id`: the folder name. A short version of the title, three to six lowercase words with hyphens: `replication-lag-pt-heartbeat`, not the whole title and not the draft's filename. No date in it. Set it once and never change it: a new `id` makes a new post.
- `slug`: leave it out. The public address is `percona.com/blog/<id>/`.
- `date`: any time near today. It is only for the preview. The real date is written when the post is published.
- `draft: false` for a post that should be published.
- `origin`: follows the author, not the topic. A `staff` author writes `percona` posts, a `community` author writes `community` posts.
- `description`: one or two sentences. The author's opening lines, lightly trimmed, are fine.
- `authors`: author ids, not display names. A `percona` post lists only `staff` authors.
- `categories`: one to three names, copied exactly from `tools/data/wp-categories.txt`. Start with the database, then a Percona product or a topic if the post is about one. Do not invent a name. If nothing fits, say so in the pull request.
- `tags`: two to five. Reuse the spelling other posts already use. Do not repeat the category, the author's name, or the word Percona alone. Product names such as `Percona Toolkit` or `pt-heartbeat` are good tags.
- `images`: the first file is the cover, 1200×630. Do not list an inline picture here. If there is no cover yet, leave `images` out entirely and say so in the pull request.

## Text

- Do not start the text with `# Title`. The title comes from `title`. Sections start at `##`.
- Images sit next to `index.md` and are linked by filename: `![What the picture shows](diagram.png)`. About 1600px wide is enough. Keep each file around 200–400 KB. Use JPEG or WebP for photos, PNG or WebP for screenshots.
- If a picture does not match what the text says about it, keep it, and point it out in the pull request. Do not redraw or replace it.
- A diagram can be a `mermaid` code block instead of a screenshot. The preview draws it.
- Code blocks name the language: ```` ```sql ````, ```` ```bash ````.

## Author page

Path: `authors/<author-id>/index.md`. Copy the shape of an existing one in `authors/`.

The folder name is the id: `name-surname`, lowercase letters, digits, hyphens. Not `name_surname`, not `name.surname`, no capitals. `name` is the display name. `type` is `staff` or `community`. The portrait sits in the same folder, square, about 400px, and `image` is its filename. The text under the front matter is the bio.

## Run it locally

You need [Hugo](https://gohugo.io/) 0.168 or newer (`brew install hugo` on a Mac) and Python 3. From the repository root:

```bash
make -C tools serve    # preview at http://localhost:1314/ , drafts included
make -C tools check    # must pass before the pull request
```

`serve` keeps running until you stop it. `check` can run while it is running.

`check` fails on a missing author page, a bad author id, a category that is not on the list, or an image the text names that is not next to the post. The message names the file. Fix the post or the author page. If the failure points at `tools/` or at another post, stop and tell the author.

## After the pull request

A comment on the pull request links to a preview of the post. Each new commit on the same branch updates it. The post is merged after three approvals from people who know the subject.

To change a published post in the first few days, open a new pull request on a branch named `fix/<id>`. After that, the post may have been polished in WordPress, and the repository no longer updates it. Ask the author to open an issue instead.
