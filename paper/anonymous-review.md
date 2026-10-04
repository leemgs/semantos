# Anonymous artifact link for ARR review

The paper says that prompts, raw responses, per-claim annotations and logs are
released. Reviewers must be able to see them without learning who the authors
are. This note explains how to produce the anonymized copy and the link.

## 1. Build the anonymized copy

```
python3 scripts/make_anonymous_release.py --out /tmp/semantos-anon --zip
```

The script exports the tracked files of `HEAD` without git history and leaves
out:

| Excluded path | Why |
|---|---|
| `archive/` | earlier submission, slides and posters with the author's name and e-mail |
| `ppt/` | pointer to the archived slides |
| `REVIEW_*.md` | responses to the earlier venue's reviews (identifies the earlier submission) |
| `code/legacy/` | superseded prototype; its docstring names the earlier submission |
| `paper/aaai2027.bib` | leftover template file from the earlier venue |
| `paper/responsible-nlp-checklist.md`, this file, the script itself | internal notes; the script lists the identifying terms |

The public project name "SemantOS" leads to the authors' public repository, so
the paper calls the system GroundKern (macro `\sysname` in `main.tex`) and the
script replaces SemantOS/semantos with GroundKern/groundkern in every released
file's contents and path; the logo, which shows the old name, is left out.

It then scans every remaining text file, and the text of every PDF, for the
author's name, user name and e-mail, the old project name, the earlier venue
and submission number, home-directory paths and session links, and aborts
without writing anything if one is found.

Re-run the script after every change and before uploading.

## 2. Upload as supplementary material

The authors decided not to use an anonymous mirror service. The zip from step 1
is uploaded to OpenReview as ARR supplementary material (software and data);
the paper says the artifacts are "provided as supplementary material". The
`anonymous-review` branch is no longer needed; it is to be deleted in the
GitHub web interface (the session proxy does not permit branch deletion).

Before uploading, rebuild the zip from the final commit and check that it
contains `README.md`, `code/evaluation/` and `paper/`, and that the build
reported no identifying content.

