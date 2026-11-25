# andrewsteck.github.io

Source for Andrew Steck's academic website.
The site is one page, `index.html`, served by GitHub Pages from the `master` branch.

## How it is put together

Since November 2026 the page is assembled on the computer, not by GitHub.
A short Python script reads the content from one file and the design from another, and writes the finished page.
GitHub serves that page exactly as it is.

| file | what it is | edit it? |
|---|---|---|
| `content.toml` | everything that changes: bio, links, papers, abstracts, teaching, addresses | yes, this is the file to edit |
| `tools/build.py` | the script that writes the page | rarely |
| `tools/style.css` | the design: colours, type, layout | only to change the look |
| `index.html` | the finished page | no, it is rewritten on every build |
| `research.html`, `code.html` | send old links to `/research` and `/code` on to the home page | no, also generated |
| `fonts/` | the Newsreader typeface files and their licence | no |
| `uploads/` | the CV, paper drafts, and files used by course slides | add and replace files; do not rename (see below) |
| `.nojekyll` | tells GitHub to serve the files as they are | no |

## Changing the site

1. Edit `content.toml`.
2. Run `python3 tools/build.py` (Python 3.11 or later; nothing to install).
3. Open `index.html` in a browser and look at it.
4. Commit and push. The live site updates a minute or two after the push.

The script prints a warning if a linked file is missing from the folder, and lists co-authors who have no web page recorded.
If something is wrong enough that the page would be broken (a paper in a section that does not exist, a missing title or year), it says so and writes nothing.

### Add a paper

Copy a `[[paper]]` block in `content.toml` and change it.
Papers appear in the order they are written, within their section.
Only `section`, `title` and `year` are required.

```toml
[[paper]]
section = "wp"                      # pub, wp, wip or hib (the [[section]] list defines these)
title = "Title of the Paper"
year = 2027
authors = ["First Co-author", "Second Co-author"]
status = "R&R at Journal Name"      # for a published paper use journal and journal_detail instead
notes = ["NBER Working Paper 12345"]
links = [
  { label = "Draft", url = "uploads/paper_draft.pdf" },
]
topics = ["Energy"]
abstract = """
One sentence per line is easiest to edit.
The script joins the lines into one paragraph.
"""
```

A co-author's name becomes a link when the name, spelled the same way, has an entry under `[coauthors]`.
An entry is either one address, or a table that adds a second link shown in brackets after the name:

```toml
[coauthors]
"First Co-author" = "https://example.org/"
"Second Co-author" = { url = "https://example.org/", also = "Emory", also_url = "https://example.edu/profile" }
```

### Other common changes

- **New CV.** Replace `uploads/steck_cv.pdf` with the new file under the same name. No build is needed, only commit and push.
- **New draft of a paper.** Put the PDF in `uploads/` and point the paper's link at it.
- **A paper is published.** Change `section` to `"pub"`, replace `status` with `journal` and `journal_detail`, and add a link to the published version.
- **Topic labels.** `show_topics = false` near the top of `content.toml` hides them all.
- **Colours.** The two palettes are at the top of `tools/style.css`. The dark palette is written twice and both copies must match; the script checks.
- **The "Updated" date** on the page is the month of the last build.

## Things to leave alone

- **File names under `uploads/`.** Course slides load files from `uploads/mgt371_slide_resources/`, and links elsewhere on the web may point at older PDFs in `uploads/`. Adding and replacing files is fine; renaming or deleting them breaks those links.
- **`index.html`, `research.html` and `code.html`.** Changes made there by hand are lost at the next build.

## Design notes

- One page, with the identity and links in a sidebar that becomes a header block on a phone.
- Dark mode follows the reader's system setting. The button in the sidebar switches it and the browser remembers the choice; switching back to match the system makes it automatic again.
- The page works without JavaScript (the button is then hidden).
- The Newsreader typeface is served from the site's own `fonts/` folder (downloaded from Google Fonts in November 2026, SIL Open Font License), so the page loads nothing from other sites.

## History

Until November 2026 the site was built by Jekyll on GitHub, from Markdown files and a fork of the Minimal theme, inspired by Tyler Ransom's site.
It was changed so that the page can be looked at on the computer before it is published.
