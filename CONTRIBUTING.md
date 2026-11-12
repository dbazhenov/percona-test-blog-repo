# Contributing a post

All the rules for a post, in one place. For the big picture, start with the [README](README.md). For a walkthrough, read the example for [Perconians](posts/2026/how-a-perconian-publishes/index.md) or for [community authors](posts/2026/community-post-from-a-fork/index.md).

## Before you start

- **Perconians** create a branch in this repository. If you cannot push, ask the blog team to add you to the Perconians group.
- **Community authors** fork the repository and work in the fork. The [community example](posts/2026/community-post-from-a-fork/index.md) explains forking, SSH keys, and pushing step by step.

Name the branch `blog/<post-id>`, for example `blog/replication-lag-pt-heartbeat`. A fix to a published post goes on `fix/<post-id>`.

## Files

```text
posts/2026/replication-lag-pt-heartbeat/
  index.md          the post
  cover.png         the cover, 1200×630
  lag-chart.png     pictures from the text
authors/mateo-alvarez/
  index.md          the author page, only with your first post
  avatar.png        a square portrait
```

- The folder name is the post id: a short version of the title, three to six lowercase words with hyphens. No date in it.
- The easiest start is to copy the folder of the closest example post and replace the text, pictures, and fields. Do not copy older imported posts: many have a date in the folder name and a `slug`, which new posts do not need.

## Front matter

The top of `index.md`, between two `---` lines:

```yaml
---
title: "Measuring replication lag with pt-heartbeat"
id: replication-lag-pt-heartbeat
date: "2026-11-12T09:00:00-08:00"
draft: false
origin: percona
description: "One or two sentences. This is the summary on the blog."
authors:
  - daniil-bazhenov
categories:
  - MySQL
tags:
  - replication
  - pt-heartbeat
images:
  - cover.png
---
```

| Field | Required | What to put there |
| --- | --- | --- |
| `title` | Yes | The title of the post. It becomes the heading of the page. |
| `id` | Yes | The folder name. Never change it after publication: a new `id` makes a new post. It is also the address: `percona.com/blog/<id>/`. |
| `date` | Yes | Any time near today. It is only for the preview. The real date is set when the post is published. |
| `draft` | Yes | `false` to publish. `true` keeps the post off the blog. |
| `origin` | Yes | `percona` for Perconians, `community` for community authors. |
| `description` | No | One or two sentences for the post list. Without it, the first paragraph is used. |
| `authors` | Yes | Author ids from `authors/`, not display names. A `percona` post lists only `staff` authors. |
| `categories` | Yes | One to three names from the list below. |
| `tags` | No | Two to five tags. See below. |
| `images` | Yes | The cover first. If you have no cover, leave `images` out and say so in the pull request; the team will make one. |

To take a published post down, set `draft: true` and keep the file. Deleting the file leaves the post on the blog.

## Categories

Copy the name exactly. The list lives in [`tools/data/wp-categories.txt`](tools/data/wp-categories.txt).

| Group | Categories |
| --- | --- |
| Databases | MySQL, MariaDB, PostgreSQL, MongoDB, Valkey |
| Percona products | Percona Server for MySQL, XtraDB Cluster (PXC), Xtrabackup, Percona Monitoring and Management, ProxySQL, Percona Software, Percona Services |
| Topics | Kubernetes, Operator, Cloud, Security, Monitoring, Benchmarks, AI & Vector, Storage Engine, Open Source, Insight for DBAs, Insight for Developers, Database Trends |

Start with the database. Add a product or a topic only if the post is about it. If nothing fits, do not invent a name; ask in the pull request.

## Tags

- Two to five tags.
- Reuse the spelling other posts already use. One tag `Benchmarks` is useful; `Benchmarks`, `Benchmarking`, and `benchmark` side by side are not.
- Name the tool or feature: `pgvector`, `InnoDB`, `replication`, `Percona Toolkit`.
- Do not repeat the category, your name, or the word Percona alone.

## Text

- Do not start with `# Title`. The title comes from `title`. Sections start at `##`.
- Name the language of code blocks: ```` ```sql ````, ```` ```bash ````.
- A diagram can be a [Mermaid](https://mermaid.js.org/intro/syntax-reference.html) block instead of a screenshot. The preview draws it.
- The [Perconian example](posts/2026/how-a-perconian-publishes/index.md) ends with every formatting element a post can use.

## Images

- Put pictures next to `index.md` and link them by filename: `![What the picture shows](lag-chart.png)`.
- The cover is 1200×630, the size used when the post is shared.
- The text column is 855px wide, so about 1600px wide is enough. Use JPEG or WebP for photos, PNG or WebP for screenshots.
- Keep each file around 200–400 KB. A file of 3–4 MB is too heavy.

## Author page

With your first post, add `authors/<name-surname>/index.md`:

```yaml
---
id: mateo-alvarez
name: "Mateo Alvarez"
type: community
role: "Database engineer"
company: "Fieldnote Analytics"
github: "https://github.com/..."
linkedin: "https://www.linkedin.com/in/..."
image: avatar.png
---

A few sentences about you. This is the bio under your posts.
```

The id is lowercase with hyphens: `name-surname`. Not `name_surname`, not `name.surname`, no capitals. `type` is `staff` for Perconians and `community` for everyone else. The portrait is a square of about 400px next to `index.md`.

## Check and preview

The pull request does both for you: the first comment links to a preview, and the Feed check turns red if a file is wrong.

To check on your computer, install [Hugo](https://gohugo.io/) 0.168 or newer and Python 3:

```bash
make -C tools serve    # preview at http://localhost:1314/
make -C tools check    # the same check the pull request runs
```

The check catches a missing author page, a malformed author id, a category that is not on the list, and a picture the text names but that is not next to the post. It does not read the writing.

## Review

- Three approvals from people who know the subject. Ask them, or wait for the blog team to find reviewers.
- Fix comments by pushing to the same branch. The preview updates.
- No reviewers, or declined: close the pull request and try another post.

## After publication

- The first few days: change the post in a new pull request on `fix/<post-id>`.
- After that, the blog team may polish the post in WordPress, and the repository stops updating it. [Open an issue](https://github.com/dbazhenov/percona-test-blog-repo/issues/new) with a link to the post and what should change.
