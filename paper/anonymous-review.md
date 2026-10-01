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

It then scans every remaining text file for the author's name, user name and
e-mail, the earlier venue and submission number, home-directory paths and
session links, and aborts without writing anything if one is found. The
current `HEAD` passes: 189 files, about 9 MB unpacked, 1.4 MB zipped. The three
binary files (`code/semantos_logo01.png`, `paper/figures/gate_replay.pdf`,
`paper/main.pdf`) were checked by hand and carry no author metadata.

Re-run the script after every change and before uploading.

## 2. Make the link (needs the author's GitHub login)

anonymous.4open.science mirrors a GitHub repository and replaces listed terms,
but it mirrors *every* file in the chosen branch. Point it at a branch that
contains only the anonymized copy, not at `main`, because `archive/` contains
PDFs and slides with the author's name that term replacement cannot clean.

1. Put the anonymized copy on its own branch, for example `anonymous-review`,
   as a single commit with no history (or in a separate repository).
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
