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

## 2. Make the link (needs the author's GitHub login)

anonymous.4open.science mirrors a GitHub repository and replaces listed terms,
but it mirrors *every* file in the chosen branch. Point it at a branch that
contains only the anonymized copy, not at `main`, because `archive/` contains
PDFs and slides with the author's name that term replacement cannot clean.

1. The branch `anonymous-review` holds the anonymized copy as a single
   commit with no history (created 2026-10-01 from `main` at `312fe3f`). After
   changing the paper or code, rebuild the copy and replace the branch's
   contents with a new commit.
2. Sign in at https://anonymous.4open.science with GitHub and choose
   "Anonymize a repository".
3. Repository: this repository; branch: `anonymous-review`.
4. Terms to anonymize (one per line, as a second safety net): the author's
   given name, family name and GitHub user name, and the repository owner.
5. Expiration: after the ARR cycle's decision date.
6. Copy the generated URL, of the form
   `https://anonymous.4open.science/r/<id>`, and open it in a private browser
   window to check that no name appears in files, README or the page header.

## 3. Put the link in the paper

Add one sentence at the end of the abstract, or a footnote in §1:

```
Code and data: \url{https://anonymous.4open.science/r/<id>}.
```

Rebuild with `make` in `paper/` and check that the body still ends on page 8.

## Alternative: supplementary upload

ARR also accepts software and data as supplementary material. The zip from
step 1 (1.4 MB) can be uploaded directly; in that case write "Code and data are
provided as supplementary material" instead of a URL.
