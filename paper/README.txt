SemantOS — AAAI-27 Main Technical Track submission source (double-blind)
=======================================================================
Build:   make        (builds BOTH PDFs below from main.tex; see Makefile)
         A plain `pdflatex main` also works and yields the compliant main.pdf.
Style:   Official AAAI-27 Author Kit (aaai2027.sty / .bst / .bib), unmodified.
Fonts:   aaai2027.sty auto-loads newtx/helvet/courier (present on Overleaf
         and full TeX Live installs).
Layout:  7 pages main + references (9 pages total). No forbidden packages,
         no \clearpage/\pagestyle, no spacing hacks. Author block is
         auto-anonymized by the [submission] option.

Two output PDFs (`make` builds both; selected by \debugenablereferencelink):
   main.pdf           SUBMISSION  -- \debugenablereferencelink=0. No URLs, no
                      link annotations. Fully AAAI-27 compliant. UPLOAD THIS.
   main_bluelink.pdf  DEBUG-ONLY  -- \debugenablereferencelink=1. Each reference
                      URL is a BLUE, CLICKABLE link (\pdfstartlink/\pdfendlink,
                      not hyperref) so you can click-check every reference.
                      Embeds link annotations -> MUST NOT be submitted to AAAI.
   The debug build is written to a SEPARATE filename on purpose, so the
   submission file main.pdf is always the compliant, link-free build.
   Each .bib entry carries note={\refurl{<url>}}; the bst is unmodified.

Workflow:
  1) Run `make`. Open main_bluelink.pdf and click every reference URL to
     verify it (this file is for your eyes only -- never upload it).
  2) Upload main.pdf. It has ZERO link annotations by construction; you can
     confirm with any PDF inspector before submitting.
  3) Fill & upload the Reproducibility Checklist; anonymize any Code & Data
     supplement (no names/paths/git history); external repo links forbidden.
